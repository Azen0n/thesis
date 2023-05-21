import json
from typing import TypeAlias
from urllib.parse import quote
from uuid import UUID

import requests
from django.contrib.auth.models import User
from django.http import JsonResponse

from algorithm.models import Progress, UserAnswer
from answers.models import MultipleChoiceRadio, MultipleChoiceCheckbox, FillInSingleBlank, Code
from config.settings import Constants, SANDBOX_API_URL, SANDBOX_API_HEADER, SANDBOX_API_TOKEN
from courses.models import Problem, Type, Semester, THEORY_TYPES, PRACTICE_TYPES

CorrectAnswerCoefficient: TypeAlias = int
GivenAnswer: TypeAlias = MultipleChoiceRadio | list[MultipleChoiceCheckbox] | str | tuple[str, str]
ValidatedAnswer: TypeAlias = tuple[CorrectAnswerCoefficient, GivenAnswer]


def get_answer_safe_data(problem: Problem) -> dict:
    """Возвращает словарь с id и text вариантов ответа на задание
    без is_correct.
    """
    match problem.type:
        case 'Multiple Choice Radio':
            answer = {
                'type': 'Multiple Choice Radio',
                'options': [{'id': str(option.id),
                             'text': option.text} for option in
                            problem.multiplechoiceradio_set.all()]
            }
        case 'Multiple Choice Checkbox':
            answer = {
                'type': 'Multiple Choice Checkbox',
                'options': [{'id': str(option.id),
                             'text': option.text} for option in
                            problem.multiplechoicecheckbox_set.all()]
            }
        case 'Fill In Single Blank':
            answer = {
                'type': 'Fill In Single Blank',
                'problem_id': str(problem.id)
            }
        case 'Code':
            answer = {
                'type': 'Code',
                'problem_id': str(problem.id)
            }
        case _:
            answer = {}
    return answer


def validate_answer_by_type(data: dict) -> ValidatedAnswer:
    """Возвращает коэффициент правильного ответа от 0 до 1 и выбранный вариант ответа."""
    match data['type']:
        case Type.MULTIPLE_CHOICE_RADIO.value:
            return validate_multiple_choice_radio(data.get('answer_id', None))
        case Type.MULTIPLE_CHOICE_CHECKBOX.value:
            return validate_multiple_choice_checkbox(data.get('answer_id', None))
        case Type.FILL_IN_SINGLE_BLANK.value:
            return validate_fill_in_single_blank(data.get('problem_id', None),
                                                 data.get('value', None))
        case Type.CODE.value:
            return validate_code(data.get('problem_id', None), data.get('code', None))
        case other_type:
            raise ValueError(f'Неизвестный тип {other_type}.')


def validate_multiple_choice_radio(answer_id: str) -> tuple[int, MultipleChoiceRadio]:
    """Проверка ответа на задание с типом выбора одного правильного варианта.
    Возвращает коэффициент правильного ответа от 0 до 1 и выбранный вариант ответа.
    """
    answer = MultipleChoiceRadio.objects.filter(id=answer_id).first()
    if answer is None:
        raise ValueError('Не выбран вариант ответа.')
    if answer.is_correct:
        return 1, answer
    return 0, answer


def validate_multiple_choice_checkbox(answer_ids: list[str]) -> tuple[int, list[MultipleChoiceCheckbox]]:
    """Проверка ответа на задание с типом выбора нескольких вариантов ответа.
    Возвращает коэффициент правильного ответа от 0 до 1 и выбранные варианты ответа.
    """
    user_answers = MultipleChoiceCheckbox.objects.filter(id__in=answer_ids)
    if not user_answers:
        raise ValueError('Не выбраны варианты ответа')
    problem_answers = MultipleChoiceCheckbox.objects.filter(problem=user_answers.first().problem)
    correct_answers = problem_answers.filter(is_correct=True)
    answer_coefficient = 1 / correct_answers.count()
    total_coefficient = 0
    for user_answer in user_answers:
        if user_answer in correct_answers:
            total_coefficient += answer_coefficient
        else:
            total_coefficient -= answer_coefficient
    if total_coefficient > 0:
        return total_coefficient, user_answers
    else:
        return 0, user_answers


def validate_fill_in_single_blank(problem_id: str, value: str) -> tuple[int, str]:
    """Проверка ответа на задание с типом заполнения пропуска.
    Возвращает коэффициент правильного ответа от 0 до 1, если введенный ответ
    соответствует одному из допустимых вариантов и сам введенный ответ.
    """
    if value is None:
        raise ValueError('Пустой ответ')
    if not value.strip():
        raise ValueError('Пустой ответ')
    problem = Problem.objects.get(id=problem_id)
    correct_options = FillInSingleBlank.objects.filter(problem=problem)
    for option in correct_options:
        if option.text.lower() == value.lower():
            return 1, value
    return 0, value


def validate_code(problem_id: str, code: str) -> tuple[int, tuple[str, str]]:
    """Проверяет код пользователя на тестах.
    Возвращает коэффициент правильного ответа (0 или 1)
    и кортеж из отправленного кода и результата проверки.
    """
    if code is None:
        raise ValueError('Пустой ответ')
    if not code.strip():
        raise ValueError('Пустой ответ')
    problem = Problem.objects.get(id=problem_id)
    tests = Code.objects.get(problem=problem).tests
    response = requests.post(
        f'{SANDBOX_API_URL}/run_tests',
        json={
            'tests': quote(tests),
            'code': quote(code),
        },
        headers={
            SANDBOX_API_HEADER: SANDBOX_API_TOKEN,
        }
    )
    result = response.json().get('code', None)
    if result is None:
        raise ValueError('Результат проверки кода не получен.')
    coefficient = int(is_code_solved(result))
    return coefficient, (code, result)


def is_code_solved(code_test_result: str) -> bool:
    """Возвращает True, если код успешно прошел проверку на тестах или False,
    если один из тестов не пройден или возникла ошибка.
    """
    if code_test_result == 'OK':
        return True
    return False


def get_correct_answers(problem_id: UUID) -> dict:
    """Возвращает словарь с верными ответами на задание."""
    problem = Problem.objects.get(pk=problem_id)
    match problem.type:
        case Type.MULTIPLE_CHOICE_RADIO.value:
            answer = MultipleChoiceRadio.objects.get(problem=problem, is_correct=True)
            return {'is_correct': str(answer.id)}
        case Type.MULTIPLE_CHOICE_CHECKBOX.value:
            answers = MultipleChoiceCheckbox.objects.filter(problem=problem, is_correct=True)
            return {'is_correct': [str(answer.id) for answer in answers]}
        case Type.FILL_IN_SINGLE_BLANK.value:
            return {'is_correct': list(FillInSingleBlank.objects.filter(
                problem=problem).values_list('text', flat=True))}
        case Type.CODE.value:
            return {'is_correct': problem.code_set.first().tests}
        case other_type:
            raise ValueError(f'Неизвестный тип {other_type}.')


def is_parent_topic_completed(user: User, semester: Semester, problem: Problem) -> bool:
    """Возвращает True, если завершена теория по предыдущей теме задания."""
    if problem.main_topic.parent_topic is None:
        return True
    progress = Progress.objects.filter(user=user, semester=semester,
                                       topic=problem.main_topic.parent_topic).first()
    if progress.is_theory_low_reached():
        return True
    return False


def is_problem_main_topic_completed(user: User, semester: Semester, problem: Problem) -> bool:
    """Возвращает True, если соответствующая часть основной темы задания завершена."""
    progress = Progress.objects.get(user=user, semester=semester, topic=problem.main_topic)
    if problem.type in THEORY_TYPES:
        if progress.is_theory_completed():
            return True
    elif problem.type in PRACTICE_TYPES:
        if progress.is_practice_completed():
            return True
    return False


def validate_answer_user_access(user: User, semester: Semester, problem: Problem) -> JsonResponse | None:
    """Проверяет, доступно ли задание для решения текущему пользователю.
    Возвращает JsonResponse с сообщением об ошибке или None, если задание доступно.
    """
    if user not in semester.students.all():
        return JsonResponse(json.dumps({'error': 'Вы не записаны на курс.'}), safe=False)
    if not is_parent_topic_completed(user, semester, problem):
        return JsonResponse(json.dumps({'error': f'Необходимо завершить тест по теории по теме'
                                                 f' {problem.main_topic.parent_topic}.'}), safe=False)
    if problem.type in PRACTICE_TYPES:
        progress = Progress.objects.get(user=user, semester=semester, topic=problem.main_topic)
        if not progress.is_theory_low_reached():
            return JsonResponse(json.dumps({'error': 'Тест по теории не завершен.'}), safe=False)
    if is_problem_main_topic_completed(user, semester, problem):
        return JsonResponse(json.dumps({'error': 'Набран максимальный балл.'}), safe=False)
    if problem.type in PRACTICE_TYPES:
        json_response = validate_practice_problem(user, semester, problem)
        if json_response is not None:
            return json_response
    elif UserAnswer.objects.filter(problem=problem, semester=semester, user=user).exists():
        return JsonResponse(json.dumps({'error': 'Вы уже отправили решение по этому заданию.'}), safe=False)
    return None


def validate_practice_problem(user: User, semester: Semester, problem: Problem) -> JsonResponse | None:
    """Проверяет, решалось ли данное практическое задание пользователем.
    Если исчерпано количество попыток на решение задания или задание уже решено, возвращает
    JsonResponse с сообщением об ошибке.
    Если задание решается впервые, возвращает None.
    """
    if problem.type not in PRACTICE_TYPES:
        return None
    last_answer = UserAnswer.objects.filter(
        problem=problem,
        semester=semester,
        user=user
    ).order_by('-created_at').first()
    if last_answer is not None:
        if last_answer.is_solved:
            return JsonResponse(json.dumps({'error': 'Вы уже отправили решение по этому заданию.'}), safe=False)
    number_of_answers = UserAnswer.objects.filter(
        problem=problem,
        semester=semester,
        user=user
    ).count()
    if number_of_answers >= Constants.MAX_NUMBER_OF_ATTEMPTS_PER_PRACTICE_PROBLEM:
        return JsonResponse(json.dumps({'error': 'Вы истратили все попытки на решение этого задания.'}), safe=False)
    return None
