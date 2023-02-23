import math

from django.contrib.auth.models import User

from algorithm.models import UserAnswer
from config.settings import Constants
from courses.models import Difficulty, PRACTICE_TYPES, Semester

DIFFICULTY_COEFFICIENT = {
    Difficulty.EASY: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_EASY,
    Difficulty.NORMAL: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_NORMAL,
    Difficulty.HARD: Constants.ALGORITHM_DIFFICULTY_COEFFICIENT_HARD
}


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
