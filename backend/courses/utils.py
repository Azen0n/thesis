import random

from django.contrib.auth.models import User
from django.db.models import QuerySet, F
from django.utils import timezone

from algorithm.models import Progress
from config.settings import Constants
from courses.models import (Semester, Problem, THEORY_TYPES, PRACTICE_TYPES,
                            Topic, SemesterCode)


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


def get_annotated_semester_topics(user: User, semester: Semester) -> QuerySet[Topic]:
    """Добавляет поля points, theory_points и practice_points
    текущего пользователя к каждой теме.
    """
    topics = Topic.objects.filter(
        progress__semester=semester,
        progress__user=user
    ).annotate(
        points=F('progress__theory_points') + F('progress__practice_points'),
        theory_points=F('progress__theory_points'),
        practice_points=F('progress__practice_points')
    ).order_by('module__created_at', 'created_at')
    return topics


def get_semester_code_context(semester: Semester) -> dict:
    """Возвращает словарь с кодом курса, флагом того, истек ли срок действия
    текущего кода, и датами истечения срока действия кода.
    """
    code = SemesterCode.objects.get(semester=semester)
    is_code_expired = code.expired_at < timezone.now()
    default_expiration_time = timezone.now() + timezone.timedelta(weeks=1)
    if default_expiration_time > semester.ended_at:
        default_expiration_time = timezone.now()
    context = {
        'code': code.code,
        'is_code_expired': is_code_expired,
        'min_expiration_time': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        'max_expiration_time': semester.ended_at.strftime('%Y-%m-%dT%H:%M'),
        'default_expiration_time': default_expiration_time.strftime('%Y-%m-%dT%H:%M'),
    }
    return context
