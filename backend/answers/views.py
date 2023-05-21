import json
from uuid import UUID
from urllib.parse import quote

import requests
from django.http import HttpRequest, HttpResponse, JsonResponse

from answers.create_answer import create_user_answer
from answers.utils import validate_answer_by_type, validate_answer_user_access
from config.settings import SANDBOX_API_URL, SANDBOX_API_HEADER, SANDBOX_API_TOKEN
from courses.models import Semester, Problem, PRACTICE_TYPES
from courses.utils import is_problem_answered


def validate_answer(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    """Проверка ответа пользователя с записью в БД и обновлением баллов."""
    semester = Semester.objects.get(id=semester_pk)
    problem = Problem.objects.get(pk=problem_pk)
    json_response = validate_answer_user_access(request.user, semester, problem)
    if json_response is not None:
        return json_response
    try:
        data = json.loads(request.body)
        if not data.get('time_elapsed_in_seconds'):
            time_elapsed_in_seconds = None
        else:
            time_elapsed_in_seconds = data.get('time_elapsed_in_seconds')
        coefficient, answer = validate_answer_by_type(data)
        create_user_answer(request.user, semester, problem, coefficient, answer, time_elapsed_in_seconds)
        is_answered = is_problem_answered(request.user, semester, problem)
    except (ValueError, NotImplementedError) as e:
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    return JsonResponse(json.dumps({'coefficient': coefficient, 'is_answered': is_answered}), safe=False)


def run_stdin(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    """Отправляет запрос на сервер с песочницей, и проверяет код пользователя
    на введенных им входных данных."""
    semester = Semester.objects.get(id=semester_pk)
    problem = Problem.objects.get(pk=problem_pk)
    json_response = validate_answer_user_access(request.user, semester, problem)
    if json_response is not None:
        return json_response
    if problem.type not in PRACTICE_TYPES:
        return JsonResponse(json.dumps({'error': 'Задание не поддерживает проверку кода.'}), safe=False)
    try:
        data = json.loads(request.body)
        code = data.get('code', None)
        stdin = data.get('stdin', None)
        if code is None or not code.strip():
            return JsonResponse(json.dumps({'error': 'Пустой ответ.'}), safe=False)
        response = requests.post(
            f'{SANDBOX_API_URL}/run_stdin',
            json={
                'stdin': quote(stdin),
                'code': quote(code),
            },
            headers={
                SANDBOX_API_HEADER: SANDBOX_API_TOKEN,
            }
        )
    except Exception as e:
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    return JsonResponse(json.dumps(response.json()), safe=False)
