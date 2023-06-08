from django.contrib.auth.models import User

from algorithm.models import (Progress, UserWeakestLinkState, UserAnswer
                              WeakestLinkState, UserTargetPoints)
from courses.models import Semester, Problem
from courses.utils import is_problem_answered


def create_user_progress_if_not_exists(semester: Semester, user: User):
    """Создает прогресс каждой темы курса семестра."""
    UserTargetPoints.objects.get_or_create(user=user)
    for module in semester.course.module_set.all():
        for topic in module.topic_set.all():
            progress = Progress.objects.filter(user=user,
                                               semester=semester,
                                               topic=topic).first()
            if progress:
                continue
            Progress.objects.create(user=user, semester=semester, topic=topic)
    user_weakest_link_state = UserWeakestLinkState.objects.filter(
        user=user,
        semester=semester
    ).first()
    if user_weakest_link_state is None:
        UserWeakestLinkState.objects.create(user=user,
                                            semester=semester,
                                            state=WeakestLinkState.NONE)


def skip_problem(user: User, semester: Semester, problem: Problem):
    """Пропускает задание."""
    if is_problem_answered(user, semester, problem):
        return
    UserAnswer.objects.create(
        user=user,
        semester=semester,
        problem=problem,
        coefficient=0,
        is_solved=None
    )


def format_log_problem(user: User, problem: Problem) -> str:
    """Возвращает отформатированную строку с информацией
    о пользователе и задании.
    """
    return (f'{user.username:<10} {problem.title:<25} {problem.difficulty}'
            f' {truncate_string(problem.main_topic.title):<20}')


def truncate_string(string: str, max_length: int = 20) -> str:
    """Сокращает строку длиннее максимального значения."""
    if len(string) <= max_length:
        return string
    return f'{string[:max_length - 4]}…{string[-3:]}'
