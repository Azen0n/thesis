import json
import logging
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from algorithm.models import Progress, UserWeakestLinkState, WeakestLinkState, WeakestLinkTopic, WeakestLinkProblem
from algorithm.problem_selector.weakest_link import update_user_weakest_link_state
from algorithm.utils import create_user_progress_if_not_exists, skip_problem
from algorithm.problem_selector import (next_theory_problem as get_next_theory_problem,
                                        next_practice_problem as get_next_practice_problem)
from courses.models import Semester, SemesterCode, Problem
from answers.utils import get_answer_safe_data

logger = logging.getLogger(__name__)


def enroll_semester(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Записывает пользователя на курс, если он не является преподавателем."""
    if not request.user.is_authenticated:
        return JsonResponse(json.dumps({'error': 'Войдите в систему.'}), safe=False)
    semester = Semester.objects.get(pk=pk)
    if request.user in semester.teachers.all():
        return JsonResponse(json.dumps({'error': 'Вы не можете записаться на свой курс.'}), safe=False)
    if semester.students.filter(pk=request.user.pk).first() is None:
        code = json.loads(request.body).get('code', '')
        semester_code = SemesterCode.objects.filter(semester=semester).first()
        if semester_code.code != code.upper():
            return JsonResponse(json.dumps({'error': 'Неверный код.'}), safe=False)
        if semester_code.expired_at < timezone.now():
            return JsonResponse(json.dumps({'error': 'Срок действия кода истек.'}), safe=False)
        semester.students.add(request.user)
        create_user_progress_if_not_exists(semester, request.user)
    logger.info(f'(   ) {request.user.username:<10} [студент записан на курс '
                f'{semester.course.title}]')
    return JsonResponse(json.dumps({'status': '200'}), safe=False)


def next_theory_problem(request: HttpRequest,
                        semester_pk: UUID, topic_pk: UUID) -> HttpResponse:
    """Подбирает следующее теоретическое задание по теме."""
    if not request.user.is_authenticated:
        return render(request, 'error.html', {'message': 'Войдите в систему.'}, status=401)
    try:
        progress = Progress.objects.get(user=request.user,
                                        semester_id=semester_pk,
                                        topic_id=topic_pk)
        problem = get_next_theory_problem(progress)
        answer = get_answer_safe_data(problem)
        context = {
            'semester': progress.semester,
            'problem': problem,
            'answer': json.dumps(answer),
            'type': 'theory',
            'is_practice_problem': False,
            'is_adaptive': True,
        }
        return render(request, 'problem.html', context)
    except ObjectDoesNotExist:
        return render(request, 'error.html', {'message': 'Страница не найдена.'}, status=404)
    except ValueError as e:
        return render(request, 'error.html', {'message': f'{e}'})


def next_practice_problem(request: HttpRequest,
                          semester_pk: UUID) -> HttpResponse:
    """Подбирает следующее практическое задание по теме."""
    if not request.user.is_authenticated:
        return render(request, 'error.html', {'message': 'Войдите в систему.'}, status=401)
    try:
        semester = Semester.objects.get(pk=semester_pk)
        problem = get_next_practice_problem(request.user, semester)
        answer = get_answer_safe_data(problem)
        context = {
            'semester': semester,
            'problem': problem,
            'answer': json.dumps(answer),
            'type': 'practice',
            'is_practice_problem': True,
            'is_adaptive': True,
        }
        return render(request, 'problem.html', context)
    except ObjectDoesNotExist:
        return render(request, 'error.html', {'message': 'Страница не найдена.'}, status=404)
    except ValueError as e:
        return render(request, 'error.html', {'message': f'{e}'})


def skip_theory_problem(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    """Пропускает теоретическое задание и подбирает следующее. Пропуском считается
    ответ на задание, в котором значение ответа равно null.
    """
    if not request.user.is_authenticated:
        return render(request, 'error.html', {'message': 'Войдите в систему.'}, status=401)
    semester = Semester.objects.get(pk=semester_pk)
    problem = Problem.objects.get(pk=problem_pk)
    skip_problem(request.user, semester, problem)
    logger.info(f'(   ) {request.user.username:<10} [задание {problem.title} пропущено]')
    return next_theory_problem(request, semester_pk, problem.main_topic.pk)


def skip_practice_problem(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    """Пропускает практическое задание и подбирает следующее. Пропуском считается
    ответ на задание, в котором значение ответа равно null.
    """
    if not request.user.is_authenticated:
        return render(request, 'error.html', {'message': 'Войдите в систему.'}, status=401)
    semester = Semester.objects.get(pk=semester_pk)
    problem = Problem.objects.get(pk=problem_pk)
    skip_problem(request.user, semester, problem)
    logger.info(f'(   ) {request.user.username:<10} [задание {problem.title} пропущено]')
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=request.user, semester=semester).state
    if user_weakest_link_state == WeakestLinkState.IN_PROGRESS:
        WeakestLinkTopic.objects.filter(user=request.user, semester=semester).delete()
        WeakestLinkProblem.objects.filter(user=request.user, semester=semester).delete()
        update_user_weakest_link_state(request.user, semester, WeakestLinkState.NONE)
    return next_practice_problem(request, semester_pk)
