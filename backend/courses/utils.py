import random
import re

from django.contrib.auth.models import User

from algorithm.models import Progress, UserAnswer
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


def is_problem_answered(user: User, semester: Semester, problem: Problem) -> bool:
    """Возвращает True, если на задание дан ответ."""
    if problem.type in PRACTICE_TYPES:
        return UserAnswer.objects.filter(
            user=user,
            semester=semester,
            problem=problem
        ).count() >= Constants.MAX_NUMBER_OF_ATTEMPTS_PER_PRACTICE_PROBLEM or any(
            UserAnswer.objects.filter(
                user=user,
                semester=semester,
                problem=problem
            ).values_list('is_solved', flat=True)
        )
    else:
        return UserAnswer.objects.filter(
            user=user,
            semester=semester,
            problem=problem
        ).exists()


def get_first_test(problem: Problem) -> dict | None:
    """Возвращает словарь с input и output первого теста или None,
    если количество проверочных тестов равно одному.
    """
    test_example = None
    if problem.type in PRACTICE_TYPES:
        stdin_stdout = re.split(r'\n', problem.code_set.first().tests)
        if len(stdin_stdout) > 2:
            test_example = {
                'input': stdin_stdout[0],
                'output': stdin_stdout[1],
            }
    return test_example
