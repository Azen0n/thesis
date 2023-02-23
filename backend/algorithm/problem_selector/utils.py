import math

from django.contrib.auth.models import User
from django.db.models import QuerySet, Q

from algorithm.models import Progress, UserAnswer
from config.settings import Constants
from courses.models import Difficulty, Problem, THEORY_TYPES, PRACTICE_TYPES, Semester, Topic

DIFFICULTY_COEFFICIENT = {
    Difficulty.EASY: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_EASY,
    Difficulty.NORMAL: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_NORMAL,
    Difficulty.HARD: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_HARD
}


def filter_theory_problems(progress: Progress) -> QuerySet[Problem]:
    """Возвращает теоретические задания, доступные для текущей темы пользователя
    упорядоченные в порядке убывания сложности.
    """
    difficulty = get_suitable_problem_difficulty(progress.skill_level)
    problems = filter_problems(progress.user, progress.semester, difficulty).filter(
        main_topic=progress.topic,
        type__in=THEORY_TYPES
    ).order_by('-difficulty')
    return problems


def filter_practice_problems(user: User, semester: Semester) -> QuerySet[Problem]:
    """Возвращает практические задания, доступные для текущего пользователя
    упорядоченные в порядке убывания сложности.
    """
    available_progresses = Progress.objects.filter(
        user=user,
        theory_points__gte=get_theory_threshold_low(),
        practice_points__lt=Constants.TOPIC_PRACTICE_MAX_POINTS,
        semester=semester
    )
    if not available_progresses:
        raise NotImplementedError('Необходимо завершить тест'
                                  ' по теории хотя бы по одной теме.')
    problems = Problem.objects.none()
    for progress in available_progresses:
        problems |= filter_problems(
            user,
            semester,
            get_suitable_problem_difficulty(progress.skill_level)
        ).filter(
            main_topic=progress.topic,
            type__in=PRACTICE_TYPES
        )
    return problems


def filter_problems(user: User, semester: Semester, max_difficulty: Difficulty) -> QuerySet[Problem]:
    """Возвращает теоретические и практические задания, доступные для текущего пользователя
    упорядоченные в порядке убывания сложности.
    """
    threshold_low = get_theory_threshold_low()
    topics_with_completed_theory = Topic.objects.filter(
        progress__user=user,
        progress__theory_points__gte=threshold_low,
        progress__semester=semester
    )
    problems = Problem.objects.filter(
        ~Q(useranswer__user=user),
        Q(sub_topics__isnull=True) | Q(sub_topics__in=topics_with_completed_theory),
        difficulty__lte=max_difficulty,
    ).order_by('-difficulty')
    return problems


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


def get_last_user_answer(user: User, semester: Semester) -> UserAnswer | None:
    """Возвращает последний ответ пользователя на практическое задание."""
    return UserAnswer.objects.filter(
        user=user,
        semester=semester,
        problem__type__in=PRACTICE_TYPES
    ).order_by('-created_at').first()
