import json
import logging
from uuid import UUID
from urllib.parse import quote

import requests
from django.db.models import QuerySet, Model
from django.http import HttpRequest, HttpResponse, JsonResponse

from algorithm.utils import format_log_problem
from answers.create_answer import create_user_answer
from answers.utils import validate_answer_by_type, validate_answer_user_access
from config.settings import SANDBOX_API_URL, SANDBOX_API_HEADER, SANDBOX_API_TOKEN
from courses.models import Semester, Problem, PRACTICE_TYPES
from courses.utils import is_problem_answered

logger = logging.getLogger(__name__)


def validate_answer(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    """Проверка ответа пользователя с записью в БД и обновлением баллов."""
    semester = Semester.objects.get(id=semester_pk)
    problem = Problem.objects.get(pk=problem_pk)
    json_response = validate_answer_user_access(request.user, semester, problem)
    if json_response is not None:
        return json_response
    try:
        data = json.loads(request.body)
        time_elapsed_in_seconds = data.get('time_elapsed_in_seconds')
        coefficient, answer = validate_answer_by_type(data)
        create_user_answer(request.user, semester, problem, coefficient, answer, time_elapsed_in_seconds)
        is_answered = is_problem_answered(request.user, semester, problem)
    except (ValueError, NotImplementedError) as e:
        logger.error(f'( ! ) {format_log_problem(request.user, problem)}'
                     f' [ошибка во время проверки задания] '
                     f'payload {json.loads(request.body)} error {e}')
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    if type(answer) == QuerySet:
        answer = [str(ans.id) for ans in answer]
    if isinstance(answer, Model):
        answer = str(answer.id)
    json_data = json.dumps({
        'coefficient': coefficient,
        'is_answered': is_answered,
        'answer': answer}
    )
    logger.info(f'(   ) {format_log_problem(request.user, problem)}'
                f' [проверка задания]'
                f' response {json_data}')
    return JsonResponse(json_data, safe=False)


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
        logger.error(f'( ! ) {format_log_problem(request.user, problem)}'
                     f' [ошибка во время запуска кода] '
                     f'payload {json.loads(request.body)} error {e}')
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    logger.info(f'(   ) {format_log_problem(request.user, problem)}'
                f' [запуск кода]'
                f' code {code} stdin {stdin}'
                f' response {response.json()}')
    return JsonResponse(json.dumps(response.json()), safe=False)
