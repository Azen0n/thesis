import json
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from algorithm.models import Progress
from algorithm.utils import create_user_progress_if_not_exists
from algorithm.problem_selector import (next_theory_problem as get_next_theory_problem,
                                        next_practice_problem as get_next_practice_problem)
from courses.models import Semester, SemesterCode
from answers.utils import get_answer_safe_data


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
        }
        return render(request, 'problem.html', context)
    except ObjectDoesNotExist:
        return render(request, 'error.html', {'message': 'Страница не найдена.'}, status=404)
    except NotImplementedError as e:
        return render(request, 'error.html', {'message': f'{e}'})


def next_practice_problem(request: HttpRequest,
                          semester_pk: UUID) -> HttpResponse:
    """Подбирает следующее теоретическое задание по теме."""
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
        }
        return render(request, 'problem.html', context)
    except ObjectDoesNotExist:
        return render(request, 'error.html', {'message': 'Страница не найдена.'}, status=404)
    except NotImplementedError as e:
        return render(request, 'error.html', {'message': f'{e}'})
