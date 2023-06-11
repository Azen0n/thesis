import random
import re

from django.contrib.auth.models import User
from django.db.models import QuerySet, F
from django.utils import timezone

from algorithm.models import Progress, UserAnswer
from config.settings import Constants
from courses.models import Semester, Problem, THEORY_TYPES, PRACTICE_TYPES, Topic, SemesterCode


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
        user_answers = UserAnswer.objects.filter(
            user=user,
            semester=semester,
            problem=problem,
            is_solved__isnull=False
        )
        is_practice_answered = user_answers.count() >= Constants.MAX_NUMBER_OF_ATTEMPTS_PER_PRACTICE_PROBLEM
        is_solved = any(user_answers.values_list('is_solved', flat=True))
        return is_practice_answered or is_solved
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


def get_annotated_semester_topics(user: User, semester: Semester) -> QuerySet[Topic]:
    """Добавляет поля points, theory_points и practice_points
    текущего пользователя к каждой теме.
    """
    if user not in semester.teachers.all():
        topics = Topic.objects.filter(
            progress__semester=semester,
            progress__user=user
        ).annotate(
            points=F('progress__theory_points') + F('progress__practice_points'),
            theory_points=F('progress__theory_points'),
            practice_points=F('progress__practice_points')
        ).order_by('module__created_at', 'created_at')
    else:
        topics = Topic.objects.filter(
            progress__semester=semester
        ).distinct().order_by('module__created_at', 'created_at')
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


def is_parent_topic_theory_low_reached(user: User, semester: Semester, topic: Topic) -> bool:
    """Возвращает True, если по теории предыдущей темы набран минимальный балл."""
    parent_topic_progress = Progress.objects.filter(
        semester=semester, user=user, topic=topic.parent_topic
    ).first()
    if parent_topic_progress is not None:
        if not parent_topic_progress.is_theory_low_reached():
            return False
    return True
