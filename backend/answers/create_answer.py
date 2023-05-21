from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet

from algorithm.models import UserAnswer, Progress, UserWeakestLinkState, WeakestLinkState
from algorithm.problem_selector.utils import get_last_theory_user_answers
from algorithm.problem_selector.weakest_link import (check_weakest_link,
                                                     start_weakest_link_when_ready,
                                                     stop_weakest_link_when_practice_completed)
from config.settings import Constants
from .models import Answer, CodeAnswer
from courses.models import Problem, Semester, PRACTICE_TYPES, Type, THEORY_TYPES, Difficulty
from .points_management import add_points_for_problem, add_placement_points_for_problem
from .utils import GivenAnswer

DIFFICULTY_COEFFICIENT = {
    Difficulty.EASY.value: Constants.ALGORITHM_CORRECT_ANSWER_BONUS_EASY,
    Difficulty.NORMAL.value: Constants.ALGORITHM_CORRECT_ANSWER_BONUS_NORMAL,
    Difficulty.HARD.value: Constants.ALGORITHM_CORRECT_ANSWER_BONUS_HARD,
}


@transaction.atomic
def create_user_answer(user: User, semester: Semester, problem: Problem,
                       coefficient: float, answer: GivenAnswer, time_elapsed_in_seconds: float | None):
    """Создает ответ пользователя на задание и добавляет баллы в его
    главную тему и подтемы.
    """
    is_solved = coefficient >= Constants.MIN_CORRECT_ANSWER_COEFFICIENT
    is_weakest_link_done = False
    if problem.type in PRACTICE_TYPES:
        is_weakest_link_done = check_weakest_link(user, semester, problem, is_solved)
    user_answer = UserAnswer.objects.create(
        user=user,
        semester=semester,
        problem=problem,
        is_solved=is_solved,
        coefficient=coefficient,
        time_elapsed_in_seconds=time_elapsed_in_seconds
    )
    create_given_user_answers(problem.type, answer, user_answer)
    progress = Progress.objects.filter(
        user=user,
        semester=semester,
        topic=problem.main_topic
    ).first()
    if problem.type in THEORY_TYPES:
        last_answers = get_last_theory_user_answers(user, problem.main_topic)
        if len(last_answers) < Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_ANSWERS:
            if is_solved:
                add_placement_points_for_problem(progress, user_answer)
            return
        if len(last_answers) == Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_ANSWERS:
            if is_solved:
                add_placement_points_for_problem(progress, user_answer)
            placement_change_skill_level(progress, last_answers)
            return
    change_user_skill_level(progress, user_answer)
    if is_solved:
        add_points_for_problem(user, semester, problem, coefficient)
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester)
    if user_weakest_link_state.state == WeakestLinkState.NONE and not is_weakest_link_done:
        start_weakest_link_when_ready(user, semester)
    stop_weakest_link_when_practice_completed(user, semester)


def create_given_user_answers(problem_type: str,
                              answer: GivenAnswer,
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
            code_answer = CodeAnswer.objects.create(
                code=user_answer.problem.code_set.first(),
                user_code=answer[0],
                tests_result=answer[1]
            )
            Answer.objects.create(code_answer=code_answer, user_answer=user_answer)
        case other_type:
            raise ValueError(f'Неизвестный тип {other_type}.')


def placement_change_skill_level(progress: Progress, last_answers: QuerySet[UserAnswer]):
    """На основе калибровки изменяет уровень знаний по теме."""
    longest_streak = calculate_longest_solved_streak(last_answers)
    progress.skill_level += (longest_streak * Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_BONUS
                             - Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_BIAS)
    progress.save()


def calculate_longest_solved_streak(last_answers: QuerySet[UserAnswer]) -> float:
    """Возвращает наибольшую сумму коэффициентов правильно решенных заданий подряд."""
    longest_streak = 0.0
    current_streak = 0.0
    for answer in last_answers:
        if answer.is_solved:
            current_streak += answer.coefficient
        else:
            longest_streak = max(longest_streak, current_streak)
            current_streak = 0.0
    return max(longest_streak, current_streak)


def change_user_skill_level(progress: Progress, user_answer: UserAnswer):
    """Изменяет уровень знаний пользователя по текущей теме в зависимости от
    правильности ответа на задание и его сложности.
    """
    difficulty_coefficient = DIFFICULTY_COEFFICIENT[user_answer.problem.difficulty]
    if user_answer.is_solved:
        progress.skill_level += difficulty_coefficient
    else:
        progress.skill_level -= difficulty_coefficient
    progress.save()
