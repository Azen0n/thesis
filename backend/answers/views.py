import json
from uuid import UUID

from django.http import HttpRequest, HttpResponse, JsonResponse

from answers.models import FillInSingleBlank, MultipleChoiceRadio, MultipleChoiceCheckbox
from courses.models import Semester, Problem, Type


def validate_answer(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    data = json.loads(request.body)
    try:
        coefficient = validate_answer_by_type(data)
    except ValueError as e:
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    semester = Semester.objects.filter(id=semester_pk).first()
    user = request.user
    return JsonResponse(json.dumps({'coefficient': coefficient,
                                    'correct_answers': get_correct_answers(problem_pk,
                                                                           coefficient),
                                    'semester': semester.course.title,
                                    'user': user.username}), safe=False)


def validate_answer_by_type(data: dict) -> int:
    """Возвращает TODO explain this shit"""
    match data['type']:
        case Type.MULTIPLE_CHOICE_RADIO.value:
            coefficient = validate_multiple_choice_radio(data.get('answer_id', None))
        case Type.MULTIPLE_CHOICE_CHECKBOX.value:
            coefficient = validate_multiple_choice_checkbox(data.get('answer_id', None))
        case Type.FILL_IN_SINGLE_BLANK.value:
            coefficient = validate_fill_in_single_blank(data.get('problem_id', None),
                                                        data.get('value', None))
        case Type.CODE.value:
            raise NotImplementedError('Проверки практических заданий нет.')
        case other_type:
            raise ValueError(f'Неизвестный тип {other_type}')
    return coefficient


def validate_multiple_choice_radio(answer_id: str) -> int:
    """Проверка ответа на задание с типом выбора одного правильного варианта.
    Возвращает TODO explain this shit
    """
    answer = MultipleChoiceRadio.objects.filter(id=answer_id).first()
    if answer is None:
        raise ValueError('Не выбран вариант ответа')
    if answer.is_correct:
        return 1
    return 0


def validate_multiple_choice_checkbox(answer_ids: list[str]) -> int:
    """Проверка ответа на задание с типом выбора нескольких вариантов ответа.
    Возвращает коэффициент TODO explain this shit.
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
    return total_coefficient if total_coefficient > 0 else 0


def validate_fill_in_single_blank(problem_id: str, value: str) -> int:
    """Проверка ответа на задание с типом заполнения пропуска. Возвращает коэффициент TODO explain this shit,
    если введенный ответ соответствует одному из допустимых вариантов.
    """
    if value is None:
        raise ValueError('Пустой ответ')
    if not value.strip():
        raise ValueError('Пустой ответ')
    problem = Problem.objects.get(id=problem_id)
    correct_options = FillInSingleBlank.objects.filter(problem=problem)
    for option in correct_options:
        if option.text.lower() == value.lower():
            return 1
    return 0


def get_correct_answers(problem_id: UUID, coefficient: float) -> dict:
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
            return {'is_correct': True if coefficient == 1.0 else False}
        case Type.CODE.value:
            raise NotImplementedError('Проверки практических заданий нет.')
        case other_type:
            raise ValueError(f'Неизвестный тип {other_type}')
