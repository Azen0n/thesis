import logging
from collections import Counter
from uuid import UUID

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet, Count

from algorithm.models import (UserAnswer, WeakestLinkProblem, UserWeakestLinkState,
                              WeakestLinkState, WeakestLinkTopic, Progress)
from algorithm.problem_selector.points_maximization import get_problems_with_max_value
from algorithm.problem_selector.topic_graph import load_topic_graph
from algorithm.problem_selector.utils import get_last_practice_user_answers, filter_practice_problems
from config.settings import Constants
from courses.models import Problem, Topic, Semester, Difficulty, PRACTICE_TYPES

DIFFICULTY_COEFFICIENT = {
    Difficulty.EASY.value: Constants.ALGORITHM_CORRECT_ANSWER_BONUS_EASY,
    Difficulty.NORMAL.value: Constants.ALGORITHM_CORRECT_ANSWER_BONUS_NORMAL,
    Difficulty.HARD.value: Constants.ALGORITHM_CORRECT_ANSWER_BONUS_HARD,
}

logger = logging.getLogger(__name__)


def start_weakest_link_when_ready(user: User, semester: Semester) -> Problem | None:
    """Заполняет очередь слабого звена, если выполнено условие
    на запуск алгоритма из get_practice_problems_for_weakest_link."""
    last_answer = get_last_practice_user_answers(user, semester).first()
    if last_answer is None:
        return
    if not last_answer.is_solved:
        if UserAnswer.objects.filter(
                user=user,
                semester=semester,
                problem=last_answer.problem
        ).count() < Constants.MAX_NUMBER_OF_ATTEMPTS_PER_PRACTICE_PROBLEM:
            return
        problems = get_practice_problems_for_weakest_link(user, semester, last_answer.problem)
        if problems is not None:
            topics = get_topics_of_problems(*problems)
            topics = remove_completed_topics(user, semester, topics)
            if not topics:
                logger.info(f'(   ) {user.username:<10}'
                            f' [поиск проблемных тем] все темы закрыты')
                return
            max_difficulty = min(problems[0].difficulty, problems[1].difficulty)
            fill_weakest_link_queue(user, semester, set(topics), Difficulty(max_difficulty))


def get_practice_problems_for_weakest_link(user: User, semester: Semester,
                                           problem: Problem) -> tuple[Problem, Problem] | None:
    """Проверяет условие на запуск алгоритма поиска слабого звена. Если
    пользователь допустил ошибку в двух похожих заданиях и не исправил ее
    (для исправления нужно правильно решить два похожих задания после
    допущенной ошибки), возвращает эти два практических задания. Если ошибка
    исправлена, возвращает None.
    """
    main_topic_answers = UserAnswer.objects.filter(
        user=user,
        problem__main_topic=problem.main_topic,
        semester=semester,
        problem__type__in=PRACTICE_TYPES
    ).order_by('-created_at').exclude(problem=problem)
    not_answered_problem_ids = get_not_answered_problem_ids(main_topic_answers)
    main_topic_answers = main_topic_answers.exclude(problem__id__in=not_answered_problem_ids)
    checked_problems = []
    number_of_solved_similar_problems = 0
    for answer in main_topic_answers:
        if problem == answer.problem:
            continue
        if is_problems_similar(problem, answer.problem):
            if answer.problem in checked_problems:
                continue
            checked_problems.append(answer.problem)
            if answer.is_solved is None:
                return None
            if not answer.is_solved:
                return problem, answer.problem
            number_of_solved_similar_problems += 1
            if number_of_solved_similar_problems == 2:
                return None
    return None


def get_not_answered_problem_ids(user_answers: QuerySet[UserAnswer]) -> list[UUID]:
    """Возвращает id заданий, у которых не исчерпан лимит попыток."""
    problems = user_answers.filter(is_solved=False).values_list('problem', flat=True)
    counter = Counter(problems)
    not_answered_problem_ids = [value for value, count in counter.items()
                                if count < Constants.MAX_NUMBER_OF_ATTEMPTS_PER_PRACTICE_PROBLEM]
    return not_answered_problem_ids


def is_problems_similar(problem1: Problem, problem2: Problem) -> bool:
    """Сравнивает два задания на сходство. Схожими считаются задания
    с одной и той же основной темой и подтемами, пересекающимися на 66%.
    """
    if problem1.main_topic != problem2.main_topic:
        return False
    topics1 = get_topics_of_problems(problem1)
    topics2 = get_topics_of_problems(problem2)
    return is_topics_similar(topics1, topics2)


def is_topics_similar(topics1: set[Topic], topics2: set[Topic]) -> bool:
    """Сравнивает два множества тем на сходство. Схожими считаются множества,
    в которых темы пересекаются на 66% и более.
    """
    intersection = topics1.intersection(topics2)
    largest_topics_length = max(len(topics1), len(topics2))
    return len(intersection) / largest_topics_length > Constants.PROBLEM_SIMILARITY_PERCENT


def remove_completed_topics(user: User, semester: Semester, topics: set[Topic]) -> QuerySet[Topic]:
    """Удаляет из списка темы, по практике которых набран максимальный балл."""
    progresses = Progress.objects.filter(
        user=user,
        semester=semester,
        topic__in=topics,
        practice_points__lt=Constants.TOPIC_PRACTICE_MAX_POINTS
    )
    return Topic.objects.filter(id__in=progresses.values_list('topic', flat=True))


@transaction.atomic
def fill_weakest_link_queue(user: User, semester: Semester,
                            topics: set[Topic], max_difficulty: Difficulty):
    """Находит похожие задания с темами неправильно решенных заданий
    problem1 и problem2, после чего помещает их в очередь слабого звена
    WeakestLinkProblem.
    """
    topic_graph = load_topic_graph(semester.course)
    topic_groups = topic_graph.split_topics_in_two_groups(topics)
    problems = filter_practice_problems(user, semester, max_difficulty)
    final_topic_groups = []
    for group_number, topic_group in enumerate(topic_groups, start=1):
        group_problems = find_problems_with_topics(topic_group, problems)
        group_problems = get_problems_with_max_value(user, semester, group_problems)
        weakest_link_problems = group_problems[:Constants.WEAKEST_LINK_MAX_PROBLEMS_PER_GROUP]
        if len(weakest_link_problems) < Constants.WEAKEST_LINK_MAX_PROBLEMS_PER_GROUP:
            continue
        for problem in weakest_link_problems:
            WeakestLinkProblem.objects.create(user=user, group_number=group_number,
                                              semester=semester, problem=problem)
        final_topic_groups.append((group_number, topic_group))
    if final_topic_groups:
        add_topics_to_weakest_link_queue(user, semester, final_topic_groups)
        update_user_weakest_link_state(user, semester, WeakestLinkState.IN_PROGRESS)
        logger.info(f'(   ) {user.username:<10} [поиск проблемных тем]'
                    f' создано групп: {len(final_topic_groups)}')
    else:
        logger.error(f'( ! ) {user.username:<10} [поиск проблемных тем]'
                     f' задания с темами групп не найдены.')


def add_topics_to_weakest_link_queue(user: User, semester: Semester,
                                     topic_groups: list[tuple[int, set[Topic]]]):
    """Добавляет потенциально проблемные темы в очередь слабого звена.

    topic_groups — список кортежей из номера группы и списка тем этой группы.
    """
    for group_number, topic_group in topic_groups:
        for topic in topic_group:
            WeakestLinkTopic.objects.create(
                user=user,
                semester=semester,
                topic=topic,
                group_number=group_number
            )


def get_topics_of_problems(*args: Problem) -> set[Topic]:
    """Возвращает список уникальных тем заданий."""
    topics = []
    for problem in args:
        topics.append(problem.main_topic)
        topics.extend(problem.sub_topics.all())
    return set(topics)


def find_problems_with_topics(topics: set[Topic],
                              problems: QuerySet[Problem]) -> QuerySet[Problem]:
    """Возвращает QuerySet с заданиями, у которых основная тема и подтемы
    находятся в topics. Задания упорядочены в порядке убывания сложности.

    problems — доступные для пользователя задания.
    """
    filtered_problem_ids = []
    for problem in problems:
        problem_topics = get_topics_of_problems(problem)
        if is_topics_similar(topics, problem_topics):
            filtered_problem_ids.append(problem.id)
    return Problem.objects.filter(id__in=filtered_problem_ids)


def change_weakest_link_problem_is_solved(user: User, semester: Semester, problem: Problem,
                                          is_solved: bool):
    """Изменяет флаг правильности ответа пользователя у задания из очереди слабого звена."""
    problem = WeakestLinkProblem.objects.get(user=user, semester=semester, problem=problem)
    problem.is_solved = is_solved
    problem.save()


def update_user_weakest_link_state(user: User, semester: Semester, state: WeakestLinkState):
    """Обновляет состояние алгоритма поиска слабого звена."""
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester)
    user_weakest_link_state.state = state
    user_weakest_link_state.save()


def delete_group_topics_and_problems_when_completed(user: User, semester: Semester):
    """Удаляет из очереди слабого звена задания и темы группы, если в ней
    достигнуто максимальное количество правильно решенных заданий.
    """
    problems = WeakestLinkProblem.objects.filter(user=user, semester=semester)
    group_numbers = problems.values_list('group_number', flat=True).distinct()
    for group_number in group_numbers:
        if is_topic_group_completed(user, semester, group_number, is_successful=True):
            delete_group_topics_and_problems(user, semester, group_number)
        elif is_topic_group_completed(user, semester, group_number, is_successful=False):
            WeakestLinkProblem.objects.filter(user=user, semester=semester,
                                              group_number=group_number).delete()


def delete_group_topics_and_problems(user: User, semester: Semester, group_number: int):
    """Удаляет темы и задания из очереди слабого звена по номеру группы."""
    WeakestLinkProblem.objects.filter(user=user, semester=semester,
                                      group_number=group_number).delete()
    WeakestLinkTopic.objects.filter(user=user, semester=semester,
                                    group_number=group_number).delete()


def is_topic_group_completed(user: User, semester: Semester, group_number: int,
                             is_successful: bool) -> bool:
    """Возвращает True, если в группе достигнуто максимальное количество
    правильно/неправильно решенных заданий.
    """
    solved_problems = WeakestLinkProblem.objects.filter(
        user=user,
        semester=semester,
        group_number=group_number,
        is_solved=is_successful
    )
    return len(solved_problems) == Constants.WEAKEST_LINK_NUMBER_OF_PROBLEMS_TO_SOLVE


def check_weakest_link(user: User, semester: Semester, problem: Problem, is_solved: bool) -> bool:
    """Проверяет статус алгоритма слабого звена и выполняет операции,
    соответствующие каждому статусу. Возвращает True, когда алгоритм заканчивается,
    в противном случае False.
    """
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester)
    if user_weakest_link_state.state == WeakestLinkState.IN_PROGRESS:
        if problem not in WeakestLinkProblem.objects.filter(user=user, semester=semester):
            return False
        weakest_link_in_progress(user, semester, problem, is_solved)
    user_weakest_link_state.refresh_from_db()
    if user_weakest_link_state.state == WeakestLinkState.DONE:
        if problem not in WeakestLinkProblem.objects.filter(user=user, semester=semester):
            return False
        weakest_link_done(user, semester)
        return True
    return False


def weakest_link_in_progress(user: User, semester: Semester, problem: Problem, is_solved: bool):
    """Устанавливает ответ пользователя на задание в очереди слабого звена,
    удаляет завершенные группы и меняет статус алгоритма, если он завершен.
    """
    change_weakest_link_problem_is_solved(user, semester, problem, is_solved)
    delete_group_topics_and_problems_when_completed(user, semester)
    problems = WeakestLinkProblem.objects.filter(user=user, semester=semester, is_solved__isnull=True)
    if not problems:
        update_user_weakest_link_state(user, semester, WeakestLinkState.DONE)


def weakest_link_done(user: User, semester: Semester):
    """Понижает уровень знаний по проблемным темам, определенным поиском слабого звена,
    удаляет темы из очереди и меняет статус алгоритма на None.
    """
    topics = WeakestLinkTopic.objects.filter(user=user, semester=semester).values_list('topic', flat=True)
    decrease_user_skill_level_after_weakest_link(user, semester, topics)
    WeakestLinkTopic.objects.filter(user=user, semester=semester, topic__in=topics).delete()
    update_user_weakest_link_state(user, semester, WeakestLinkState.NONE)


def decrease_user_skill_level_after_weakest_link(user: User, semester: Semester, topics: list[Topic]):
    """Понижает уровень знаний по проблемным темам, определенным поиском слабого звена."""
    for topic in topics:
        progress = Progress.objects.get(user=user, semester=semester, topic=topic)
        progress.skill_level -= Constants.WEAKEST_LINK_PENALTY
        progress.save()


def stop_weakest_link_when_practice_completed(user: User, semester: Semester):
    """Проверяет, завершены ли темы в списке проблемных тем. Если хотя бы
    по одной теме завершена практика, алгоритм поиска слабого звена прерывается.
    """
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester)
    if user_weakest_link_state.state == WeakestLinkState.IN_PROGRESS:
        weakest_link_topics = WeakestLinkTopic.objects.filter(user=user, semester=semester)
        progresses = Progress.objects.filter(
            user=user,
            semester=semester,
            topic__in=weakest_link_topics.values_list('topic', flat=True)
        )
        for progress in progresses:
            if progress.is_practice_completed():
                WeakestLinkTopic.objects.filter(user=user, semester=semester).delete()
                WeakestLinkProblem.objects.filter(user=user, semester=semester).delete()
                update_user_weakest_link_state(user, semester, WeakestLinkState.NONE)
                return


def next_weakest_link_problem(user: User, semester: Semester) -> Problem | None:
    """Возвращает следующее задание из очереди слабого звена.
    Если по основной теме задания набран балл на максимальную оценку,
    группа удаляется вне зависимости от количества решенных заданий.
    Если все группы удалены, возвращает None.
    """
    group_numbers = WeakestLinkProblem.objects.filter(
        user=user,
        semester=semester,
        is_solved__isnull=True
    ).order_by('group_number').values_list('group_number', flat=True).distinct()
    for group_number in group_numbers:
        weakest_link_problem = WeakestLinkProblem.objects.filter(
            user=user,
            semester=semester,
            is_solved__isnull=True,
            group_number=group_number
        ).first()
        progress = Progress.objects.get(
            user=user,
            semester=semester,
            topic=weakest_link_problem.problem.main_topic
        )
        if progress.points < Constants.TOPIC_THRESHOLD_HIGH:
            return weakest_link_problem.problem
        delete_group_topics_and_problems(user, semester, group_number)
    weakest_link_done(user, semester)
    return None
