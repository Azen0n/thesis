from django.contrib.auth.models import User

from algorithm.models import (Progress, UserWeakestLinkState, WeakestLinkState,
                              WeakestLinkProblem)
from config.settings import Constants
from courses.models import Problem, Semester, Difficulty
from .points_maximization import get_problems_with_max_value
from .utils import (filter_practice_problems, filter_theory_problems,
                    get_last_theory_user_answers, filter_placement_problems,
                    increase_theory_problems_difficulty)


def next_theory_problem(progress: Progress) -> Problem:
    """Возвращает следующее теоретическое задание по текущей теме студента."""
    if progress.is_theory_completed():
        raise NotImplementedError('Тест по теории завершен.')
    if progress.topic.parent_topic is not None:
        if not progress.topic.parent_topic.progress_set.filter(
                user=progress.user, semester=progress.semester
        ).first().is_theory_low_reached():
            raise NotImplementedError(f'Необходимо завершить тест по теории по теме'
                                      f' {progress.topic.parent_topic}.')
    problems = filter_theory_problems(progress)
    problems = get_problems_with_max_value(progress.user, progress.semester, problems)
    last_answers = get_last_theory_user_answers(progress.user, progress.topic)
    if len(last_answers) < Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_ANSWERS:
        problems = filter_placement_problems(progress, problems)
    if not problems:
        problems = increase_theory_problems_difficulty(progress)
    if not problems or problems is None:
        raise NotImplementedError('Доступных теоретических заданий нет.')
    return problems[0]


def next_practice_problem(user: User, semester: Semester) -> Problem:
    """Возвращает следующее практическое задание по текущей теме студента."""
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester).state
    if user_weakest_link_state == WeakestLinkState.IN_PROGRESS:
        weakest_link_problem = WeakestLinkProblem.objects.filter(
            user=user,
            semester=semester,
            is_solved__isnull=True
        ).order_by('group_number').first()
        return weakest_link_problem.problem
    problems = filter_practice_problems(user, semester)
    if not problems:
        problems = filter_practice_problems(user, semester, max_difficulty=Difficulty.NORMAL)
    if not problems:
        problems = filter_practice_problems(user, semester, max_difficulty=Difficulty.HARD)
    problems = get_problems_with_max_value(user, semester, problems)
    if not problems:
        raise NotImplementedError('Доступных практических заданий нет.')
    return problems[0]
