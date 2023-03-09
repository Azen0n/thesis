import random

from django.contrib.auth.models import User

from algorithm.models import Progress
from config.settings import Constants
from courses.models import Semester, Problem, THEORY_TYPES, PRACTICE_TYPES


def is_problem_topic_completed(user: User, semester: Semester, problem: Problem) -> bool:
    """Возвращает True, если тема задания завершена."""
    progress = Progress.objects.get(user=user, semester=semester, topic=problem.main_topic)
    if problem.type in THEORY_TYPES:
        if progress.is_theory_completed():
            return True
    elif problem.type in PRACTICE_TYPES:
        if progress.is_practice_completed():
            return True
    return False


def generate_join_code():
    """Генерирует новый код для присоединения к курсу."""
    return ''.join(random.choices(Constants.JOIN_CODE_CHARACTERS,
                                  k=Constants.JOIN_CODE_LENGTH))
