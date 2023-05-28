from typing import Callable

from django.contrib.auth.models import User

from algorithm.models import Progress, UserWeakestLinkState, WeakestLinkState
from courses.models import Semester, Problem


def create_user_progress_if_not_exists(semester: Semester, user: User):
    """Создает прогресс каждой темы курса семестра."""
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
