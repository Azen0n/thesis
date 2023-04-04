import json
from uuid import UUID
from urllib.parse import quote

import requests
from django.http import HttpRequest, HttpResponse, JsonResponse

from answers.create_answer import create_user_answer
from answers.models import Code
from answers.utils import validate_answer_by_type, validate_answer_user_access
from courses.models import Semester, Problem, PRACTICE_TYPES


def validate_answer(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    """Проверка ответа пользователя с записью в БД и обновлением баллов."""
    semester = Semester.objects.get(id=semester_pk)
    problem = Problem.objects.get(pk=problem_pk)
    json_response = validate_answer_user_access(request.user, semester, problem)
    if json_response is not None:
        return json_response
    try:
        data = json.loads(request.body)
        coefficient, answer = validate_answer_by_type(data)
        create_user_answer(request.user, semester, problem, coefficient, answer)
    except (ValueError, NotImplementedError) as e:
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    return JsonResponse(json.dumps({'coefficient': coefficient}), safe=False)


def run_tests(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    """Отправляет запрос на сервер с песочницей, и проверяет код пользователя
    на тестах."""
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
        tests = Code.objects.filter(problem=problem).first().tests
        if code is None or not code.strip():
            return JsonResponse(json.dumps({'error': 'Пустой ответ.'}), safe=False)
        url = f'http://localhost:8080/run_tests?tests={quote(tests)}&code={quote(code)}'
        response = requests.post(url)
    except Exception as e:
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    return JsonResponse(json.dumps(response.json()), safe=False)


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
        url = f'http://172.17.0.0:8080/run_stdin?stdin={quote(stdin)}&code={quote(code)}'
        response = requests.post(url, timeout=10)
    except Exception as e:
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    return JsonResponse(json.dumps(response.json()), safe=False)
