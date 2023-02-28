import json
from uuid import UUID

from django.contrib.auth.models import User
from django.http import JsonResponse

from algorithm.models import Progress
from answers.models import MultipleChoiceRadio, MultipleChoiceCheckbox, FillInSingleBlank
from courses.models import Problem, Type, Semester, THEORY_TYPES, PRACTICE_TYPES


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
        case _:
            answer = {}
    return answer


def validate_answer_by_type(data: dict) -> tuple[int, MultipleChoiceRadio | list[MultipleChoiceCheckbox] | str]:
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
            raise NotImplementedError('Проверки практических заданий нет.')
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
