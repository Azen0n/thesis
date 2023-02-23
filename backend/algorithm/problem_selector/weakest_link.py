from django.contrib.auth.models import User
from django.db.models import QuerySet

from algorithm.models import (UserAnswer, WeakestLinkProblem,
                              UserWeakestLinkState, WeakestLinkState, WeakestLinkTopic, Progress)
from algorithm.problem_selector.topic_graph import load_topic_graph
from algorithm.problem_selector.utils import filter_practice_problems, get_last_user_answer
from config.settings import Constants
from courses.models import Problem, Topic, Semester, Difficulty


def start_weakest_link_when_ready(user: User, semester: Semester):
    """Заполняет очередь слабого звена, если выполнено условие
    на запуск алгоритма из get_practice_problems_for_weakest_link."""
    last_answer = get_last_user_answer(user, semester)
    if last_answer is None:
        return
    if not last_answer.is_solved:
        problems = get_practice_problems_for_weakest_link(user, semester, last_answer.problem)
        if problems is not None:
            topics = get_topics_of_problems(*problems)
            topics = remove_completed_topics(user, semester, topics)
            if not topics:
                return
            max_difficulty = min(problems[0].difficulty, problems[1].difficulty)
            fill_weakest_link_queue(user, semester, topics, Difficulty(max_difficulty))


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
        semester=semester
    ).order_by('-created_at')
    number_of_solved_similar_problems = 0
    for answer in main_topic_answers:
        if is_problems_similar(problem, answer.problem):
            if not answer.is_solved:
                return problem, answer.problem
            number_of_solved_similar_problems += 1
            if number_of_solved_similar_problems == 2:
                return None
    return None


def is_problems_similar(problem1: Problem, problem2: Problem) -> bool:
    """Сравнивает два задания на сходство. Схожими считаются задания
    с одной и той же основной темой и подтемами, пересекающимися на 66%.
    """
    if problem1.main_topic != problem2.main_topic:
        return False
    intersection = problem1.sub_topics.all().intersection(problem2.sub_topics.all())
    return intersection.count() / problem1.sub_topics.all().count() > 0.66


def remove_completed_topics(user: User, semester: Semester, topics: list[Topic]) -> list[Topic]:
    """Удаляет из списка темы, по практике которых набран максимальный балл."""
    progresses = Progress.objects.filter(
        user=user,
        semester=semester,
        topic__in=topics,
        practice_points=Constants.TOPIC_PRACTICE_MAX_POINTS
    )
    return progresses.values_list('topic', flat=True)


def fill_weakest_link_queue(user: User, semester: Semester,
                            topics: list[Topic], max_difficulty: Difficulty):
    """Находит похожие задания с темами неправильно решенных заданий
    problem1 и problem2, после чего помещает их в очередь слабого звена
    WeakestLinkProblem.
    """
    topic_graph = load_topic_graph(semester.course)
    topic_groups = topic_graph.split_topics_in_two_groups(topics)
    problems = filter_practice_problems(user, semester)
    for group_number, topic_group in enumerate(topic_groups, start=1):
        group_problems = find_problems_with_topics(topic_group, problems)
        weakest_link_problems = group_problems.filter(
            difficulty__lte=max_difficulty
        )[:Constants.WEAKEST_LINK_MAX_PROBLEMS_PER_GROUP]
        for problem in weakest_link_problems:
            WeakestLinkProblem.objects.create(user=user, group_number=group_number,
                                              semester=semester, problem=problem)
    if WeakestLinkProblem.objects.filter(user=user, semester=semester):
        add_topics_to_weakest_link_queue(user, semester, topic_groups)
    else:
        raise NotImplementedError('Доступные задания с темами группы не найдены.')


def add_topics_to_weakest_link_queue(user: User, semester: Semester,
                                     topic_groups: tuple[list[Topic], list[Topic]]):
    """Добавляет потенциально проблемные темы в очередь слабого звена."""
    for group_number, topic_group in enumerate(topic_groups):
        for topic in topic_group:
            WeakestLinkTopic.objects.create(
                user=user,
                semester=semester,
                topic=topic,
                group_number=group_number
            )


def get_topics_of_problems(*args: Problem) -> list[Topic]:
    """Возвращает список уникальных тем заданий."""
    topics = []
    for problem in args:
        topics.append(problem.main_topic)
        topics.extend(problem.sub_topics.all())
    return list(set(topics))


def find_problems_with_topics(topics: list[Topic],
                              problems: QuerySet[Problem]) -> QuerySet[Problem]:
    """Возвращает QuerySet с заданиями, у которых основная тема и подтемы
    находятся в topics. Задания упорядочены в порядке убывания сложности.

    problems — доступные для пользователя задания.
    """
    problems = problems.filter(main_topic__in=topics, sub_topics__in=topics)
    if len(problems) < Constants.WEAKEST_LINK_MAX_PROBLEMS_PER_GROUP:
        problems |= problems.filter(main_topic__in=topics)
        problems = problems.distinct()
    if not problems:
        raise NotImplementedError('Доступные задания с темами группы не найдены.')
    return problems.order_by('-difficulty')


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
            WeakestLinkProblem.objects.filter(user=user, semester=semester,
                                              group_number=group_number).delete()
            WeakestLinkTopic.objects.filter(user=user, semester=semester,
                                            group_number=group_number).delete()
        elif is_topic_group_completed(user, semester, group_number, is_successful=False):
            WeakestLinkProblem.objects.filter(user=user, semester=semester,
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
