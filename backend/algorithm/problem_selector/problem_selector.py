from django.contrib.auth.models import User
from django.db.models import QuerySet, Q

from algorithm.models import (Progress, UserWeakestLinkState, WeakestLinkState,
                              WeakestLinkProblem)
from config.settings import Constants
from courses.models import (Problem, Semester, Topic, Difficulty, PRACTICE_TYPES,
                            THEORY_TYPES)
from .utils import get_theory_threshold_low, get_suitable_problem_difficulty
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
