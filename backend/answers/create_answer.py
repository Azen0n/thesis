from django.contrib.auth.models import User
from django.db import transaction

from algorithm.models import UserAnswer, Progress
from algorithm.problem_selector.weakest_link import check_weakest_link
from config.settings import Constants
from .models import Answer, MultipleChoiceRadio, MultipleChoiceCheckbox
from courses.models import Problem, Semester, PRACTICE_TYPES, Type
from .points_management import add_points_for_problem


@transaction.atomic
def create_user_answer_test(user: User, semester: Semester, problem: Problem,
                            coefficient: float, answer: MultipleChoiceRadio | list[MultipleChoiceCheckbox] | str):
    """Создает ответ пользователя на задание и добавляет баллы в его
    главную тему и подтемы.
    """
    is_solved = coefficient >= Constants.MIN_CORRECT_ANSWER_COEFFICIENT
    if problem.type in PRACTICE_TYPES:
        check_weakest_link(user, semester, problem, is_solved)
    user_answer = UserAnswer.objects.create(
        user=user,
        semester=semester,
        problem=problem,
        is_solved=is_solved
    )
    create_entered_user_answers(problem.type, answer, user_answer)
    progress = Progress.objects.filter(
        user=user,
        semester=semester,
        topic=problem.main_topic
    ).first()
    change_user_skill_level(progress, is_solved)
    if is_solved:
        add_points_for_problem(user, semester, problem)


@transaction.atomic
def create_user_answer(user: User, semester: Semester, problem: Problem,
                       is_solved: bool):
    """Создает ответ пользователя на задание и добавляет баллы в его
    главную тему и подтемы.
    """
    check_weakest_link(user, semester, problem, is_solved)
    UserAnswer.objects.create(
        user=user,
        semester=semester,
        problem=problem,
        is_solved=is_solved,
        answer=Answer.objects.create(),
    )
    progress = Progress.objects.filter(
        user=user,
        semester=semester,
        topic=problem.main_topic
    ).first()
    change_user_skill_level(progress, is_solved)
    if is_solved:
        add_points_for_problem(user, semester, problem)


def create_entered_user_answers(problem_type: str,
                                answer: MultipleChoiceRadio | list[MultipleChoiceCheckbox] | str,
                                user_answer: UserAnswer):
    """Создает список Answer с выбранными/введенными ответами пользователя."""
    match problem_type:
        case Type.MULTIPLE_CHOICE_RADIO.value:
            Answer.objects.create(multiple_choice_radio=answer, user_answer=user_answer)
        case Type.MULTIPLE_CHOICE_CHECKBOX.value:
            for ans in answer:
                Answer.objects.create(multiple_choice_checkbox=ans, user_answer=user_answer)
        case Type.FILL_IN_SINGLE_BLANK.value:
            Answer.objects.create(fill_in_single_blank=answer, user_answer=user_answer)
        case Type.CODE.value:
            raise NotImplementedError('Проверки практических заданий нет.')
        case other_type:
            raise ValueError(f'Неизвестный тип {other_type}.')


def change_user_skill_level(progress: Progress, is_solved: bool):
    """Изменяет уровень знаний пользователя по текущей теме в зависимости от
    правильности ответа на задание."""
    placement_coefficient = get_skill_level_placement_coefficient(progress)
    if is_solved:
        progress.skill_level += placement_coefficient * Constants.ALGORITHM_CORRECT_ANSWER_BONUS
    else:
        progress.skill_level -= placement_coefficient * Constants.ALGORITHM_WRONG_ANSWER_PENALTY
    progress.save()


def get_skill_level_placement_coefficient(progress: Progress) -> float:
    """Калибровка уровня знаний студента. За первые несколько ответов
    пользователь получает больший прирост.

    Возвращает коэффициент прироста.
    """
    number_of_answered_problems = UserAnswer.objects.filter(
        user=progress.user,
        problem__main_topic=progress.topic
    ).order_by('-created_at').count()
    placement_answers = Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_ANSWERS
    if number_of_answered_problems < placement_answers:
        coefficient = placement_answers + 1 - number_of_answered_problems
    else:
        coefficient = 1
    return coefficient
