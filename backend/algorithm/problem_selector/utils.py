import math

from django.contrib.auth.models import User
from django.db.models import QuerySet, Q, F

from algorithm.models import UserAnswer, Progress
from algorithm.problem_selector.points_maximization import get_problems_with_max_value
from config.settings import Constants
from courses.models import (Difficulty, THEORY_TYPES, PRACTICE_TYPES, Semester,
                            Problem, Topic)

DIFFICULTY_COEFFICIENT = {
    Difficulty.EASY: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_EASY,
    Difficulty.NORMAL: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_NORMAL,
    Difficulty.HARD: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_HARD
}


def filter_theory_problems(progress: Progress) -> QuerySet[Problem]:
    """Возвращает теоретические задания, доступные для текущей темы пользователя
    упорядоченные в порядке убывания сложности.
    """
    threshold_low = get_theory_threshold_low()
    difficulty = get_suitable_problem_difficulty(progress.skill_level)
    topics_with_completed_parent_topics = Topic.objects.filter(
        Q(parent_topic__isnull=True)
        | (Q(parent_topic__progress__theory_points__gte=threshold_low)
           & Q(parent_topic__progress__user=progress.user)
           & Q(parent_topic__progress__semester=progress.semester))
    )
    problems = filter_problems(progress.user, progress.semester).filter(
        main_topic=progress.topic,
        type__in=THEORY_TYPES,
        difficulty__lte=difficulty,
        main_topic__in=topics_with_completed_parent_topics
    )
    return problems


def filter_practice_problems(user: User, semester: Semester,
                             max_difficulty: Difficulty = None) -> QuerySet[Problem]:
    """Возвращает практические задания, доступные для текущего пользователя
    упорядоченные в порядке убывания сложности.
    """
    available_progresses = get_available_progresses(user, semester)
    if not available_progresses:
        raise NotImplementedError('Необходимо завершить тест'
                                  ' по теории хотя бы по одной теме.')
    not_completed_topics_ids = Progress.objects.filter(
        user=user,
        semester=semester
    ).annotate(
        points=F('theory_points') + F('practice_points')
    ).filter(
        points__lt=Constants.TOPIC_THRESHOLD_HIGH
    ).values_list('topic__id', flat=True)
    problems = filter_problems(user, semester).filter(
        type__in=PRACTICE_TYPES,
        main_topic_id__in=not_completed_topics_ids
    )
    if max_difficulty is None:
        problems = filter_problems_with_suitable_difficulty(problems, available_progresses)
    else:
        problems = problems.filter(difficulty__lte=max_difficulty)
    return problems


def get_available_progresses(user: User, semester: Semester) -> QuerySet[Progress]:
    """Возвращает прогрессы по темам, по которым набран минимальный балл
    по теории и не завершена практика.
    """
    return Progress.objects.filter(
        user=user,
        theory_points__gte=get_theory_threshold_low(),
        practice_points__lt=Constants.TOPIC_PRACTICE_MAX_POINTS,
        semester=semester
    )


def filter_problems(user: User, semester: Semester) -> QuerySet[Problem]:
    """Возвращает теоретические и практические задания, доступные для текущего пользователя."""
    threshold_low = get_theory_threshold_low()
    topics_with_completed_theory = Topic.objects.filter(
        progress__user=user,
        progress__theory_points__gte=threshold_low,
        progress__semester=semester
    )
    problems = Problem.objects.filter(
        ~Q(useranswer__user=user),
        Q(sub_topics__isnull=True) | Q(sub_topics__in=topics_with_completed_theory)
    ).distinct()
    return problems


def filter_problems_with_suitable_difficulty(problems: QuerySet[Problem],
                                             available_progresses: QuerySet[Progress]) -> QuerySet[Problem]:
    """Возвращает задания с подходящим уровнем сложности по каждой теме."""
    appropriate_problem_ids = []
    for problem in problems:
        progress = available_progresses.filter(topic=problem.main_topic).first()
        if progress is None:
            continue
        difficulty = get_suitable_problem_difficulty(progress.skill_level)
        if problem.difficulty == difficulty.value:
            appropriate_problem_ids.append(problem.id)
    return Problem.objects.filter(id__in=appropriate_problem_ids)


def get_theory_threshold_low() -> float:
    """Возвращает минимальное количество баллов, необходимое для завершения
    теории по теме.
    """
    topic_max_points = Constants.TOPIC_THEORY_MAX_POINTS + Constants.TOPIC_PRACTICE_MAX_POINTS
    low = Constants.TOPIC_THEORY_MAX_POINTS * (Constants.TOPIC_THRESHOLD_LOW / topic_max_points)
    return low


def get_suitable_problem_difficulty(skill_level: float) -> Difficulty:
    """Возвращает уровень сложности задания, подходящий по уровню знаний студента."""
    probability = Constants.ALGORITHM_SUITABLE_DIFFICULTY_PROBABILITY
    if correct_answer_probability(skill_level, Difficulty.HARD) >= probability:
        return Difficulty.HARD
    if correct_answer_probability(skill_level, Difficulty.NORMAL) >= probability:
        return Difficulty.NORMAL
    return Difficulty.EASY


def correct_answer_probability(skill_level: float, difficulty: Difficulty) -> float:
    """Рассчитывает вероятность правильного ответа пользователем
    на задание с указанной сложностью.
    """
    return 1 / (1 + math.exp(-(skill_level - DIFFICULTY_COEFFICIENT[difficulty])))


def get_last_practice_user_answers(user: User, semester: Semester) -> QuerySet[UserAnswer]:
    """Возвращает практические задания по теме, решенные пользователем."""
    return UserAnswer.objects.filter(
        user=user,
        semester=semester,
        problem__type__in=PRACTICE_TYPES
    ).order_by('-created_at')


def get_last_theory_user_answers(user: User, topic: Topic) -> QuerySet[UserAnswer]:
    """Возвращает теоретические задания по теме, решенные пользователем."""
    return UserAnswer.objects.filter(
        user=user,
        problem__main_topic=topic,
        problem__type__in=THEORY_TYPES
    ).order_by('-created_at')


def filter_wrongly_answered_theory_problems(progress: Progress) -> QuerySet[Problem]:
    """Возвращает неправильно решенные задания по теме."""
    difficulty = get_suitable_problem_difficulty(progress.skill_level)
    solved_problems = UserAnswer.objects.filter(
        user=progress.user,
        semester=progress.semester,
        problem__type__in=THEORY_TYPES,
        problem__main_topic=progress.topic,
        problem__difficulty_lte=difficulty,
        is_solved=False
    ).order_by('-difficulty')
    return solved_problems


def filter_placement_problems(progress: Progress, problems: list[Problem]) -> list[Problem]:
    """Возвращает список теоретических заданий для калибровки."""
    difficulty = get_suitable_problem_difficulty(progress.skill_level)
    problems = list(filter(lambda x: x.difficulty <= difficulty, problems))
    problems = sorted(problems, key=lambda x: x.difficulty, reverse=True)
    return problems


def filter_theory_problems_increase_difficulty(progress: Progress) -> list[Problem] | None:
    """Повышает сложность теоретических заданий на один уровень,
    и возвращает список заданий со сложностью равной ей или ниже.
    Возвращает None, если превышена максимальная сложность.
    """
    try:
        difficulty = Difficulty(get_suitable_problem_difficulty(progress.skill_level).value + 1)
    except ValueError:
        return None
    problems = filter_problems(progress.user, progress.semester).filter(
        main_topic=progress.topic,
        type__in=THEORY_TYPES,
        difficulty__lte=difficulty
    )
    problems = get_problems_with_max_value(progress.user, progress.semester, problems)
    return problems
