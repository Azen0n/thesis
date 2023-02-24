import json
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from algorithm.models import Progress
from algorithm.utils import create_user_progress
from algorithm.problem_selector import (next_theory_problem as get_next_theory_problem,
                                        next_practice_problem as get_next_practice_problem)
from courses.models import Semester
from answers.utils import get_answer_safe_data


def enroll_semester(request: HttpRequest, pk: UUID) -> HttpResponse:
    semester = Semester.objects.get(pk=pk)
    if semester.students.filter(pk=request.user.pk).first() is None:
        semester.students.add(request.user)
        create_user_progress(semester, request.user)
    return redirect(f'/semesters/{semester.pk}')


def next_theory_problem(request: HttpRequest,
                        semester_pk: UUID, topic_pk: UUID) -> HttpResponse:
    """Подбирает следующее теоретическое задание по теме."""
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
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
        }
        return render(request, 'problem.html', context)
    except ObjectDoesNotExist:
        return HttpResponse('Не найдено', status=404)
    except NotImplementedError as e:
        return HttpResponse(f'{e}')


def next_practice_problem(request: HttpRequest,
                          semester_pk: UUID) -> HttpResponse:
    """Подбирает следующее теоретическое задание по теме."""
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    try:
        semester = Semester.objects.get(pk=semester_pk)
        problem = get_next_practice_problem(request.user, semester)
        answer = get_answer_safe_data(problem)
        context = {
            'semester': semester,
            'problem': problem,
            'answer': json.dumps(answer),
            'type': 'practice',
        }
        return render(request, 'problem.html', context)
    except ObjectDoesNotExist:
        return HttpResponse('Не найдено', status=404)
    except NotImplementedError as e:
        return HttpResponse(f'{e}')
