from django.contrib.auth.models import User
from django.db.models import QuerySet

from algorithm.models import (Progress, UserWeakestLinkState, WeakestLinkState,
                              WeakestLinkProblem)
from courses.models import Problem, Semester, THEORY_TYPES
from .utils import (get_suitable_problem_difficulty, filter_practice_problems,
                    filter_problems)
from .weakest_link import start_weakest_link_when_ready


def next_theory_problem(progress: Progress) -> Problem:
    """Возвращает следующее теоретическое задание по текущей теме студента."""
    if progress.is_theory_completed():
        raise NotImplementedError('Тест по теории завершен.')
    problem = filter_theory_problems(progress).first()
    if problem is None:
        raise NotImplementedError('Доступных теоретических заданий нет.')
    return problem


def next_practice_problem(user: User, semester: Semester) -> Problem:
    """Возвращает следующее практическое задание по текущей теме студента."""
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester).state
    if user_weakest_link_state == WeakestLinkState.IN_PROGRESS:
        return WeakestLinkProblem.objects.filter(user=user, semester=semester,
                                                 is_solved__isnull=True).first()
    if user_weakest_link_state == WeakestLinkState.DONE:
        raise NotImplementedError('Что-то пошло не так с поиском слабого звена.')
    start_weakest_link_when_ready(user, semester)
    problem = filter_practice_problems(user, semester).first()
    if problem is None:
        raise NotImplementedError('Доступных практических заданий нет.')
    return problem


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
