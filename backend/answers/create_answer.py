from django.contrib.auth.models import User
from django.db import transaction

from algorithm.models import (UserAnswer, Progress, WeakestLinkState,
                              UserWeakestLinkState)
from algorithm.problem_selector.weakest_link import (weakest_link_in_progress,
                                                     weakest_link_done)
from config.settings import Constants
from .models import Answer
from courses.models import (Problem, THEORY_TYPES, PRACTICE_TYPES,
                            Difficulty, Topic, Semester)

POINTS_BY_DIFFICULTY = {
    Difficulty.EASY: Constants.POINTS_EASY,
    Difficulty.NORMAL: Constants.POINTS_NORMAL,
    Difficulty.HARD: Constants.POINTS_HARD,
}


@transaction.atomic
def create_user_answer(user: User, semester: Semester, problem: Problem,
                       is_solved: bool):
    """Создает ответ пользователя на задание и добавляет баллы в его
    главную тему и подтемы.
    """
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester)
    if user_weakest_link_state.state == WeakestLinkState.IN_PROGRESS:
        weakest_link_in_progress(user, semester, problem, is_solved)
    user_weakest_link_state.refresh_from_db()
    if user_weakest_link_state.state == WeakestLinkState.DONE:
        weakest_link_done(user, semester)
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


def add_points_for_problem(user: User, semester: Semester, problem: Problem):
    """Добавляет баллы во все темы задания."""
    points = POINTS_BY_DIFFICULTY[Difficulty(problem.difficulty)]
    sub_topic_points = points * Constants.SUB_TOPIC_POINTS_COEFFICIENT
    add_points_to_topic(user, semester, problem.main_topic, problem, points)
    for topic in problem.sub_topics.all():
        add_points_to_topic(user, semester, topic, problem, sub_topic_points)


def add_points_to_topic(user: User, semester: Semester, topic: Topic,
                        problem: Problem, points: float):
    """Добавляет баллы в тему задания."""
    topic_progress = Progress.objects.filter(
        user=user,
        semester=semester,
        topic=topic
    ).first()
    if topic_progress is None:
        raise ValueError(f'Прогресс пользователя {user}'
                         f' по теме {topic} ({topic.id}) не найден.')
    if problem.type in THEORY_TYPES:
        add_theory_points(topic_progress, points)
    elif problem.type in PRACTICE_TYPES:
        add_practice_points(topic_progress, points)
    else:
        raise ValueError(f'Тип {problem.type} задания {problem}'
                         f' не относится к теоретическим или'
                         f' практическим типам.')


def add_theory_points(progress: Progress, points: float):
    """Добавляет баллы в прогресс пользователя по теории."""
    if progress.theory_points + points > Constants.TOPIC_THEORY_MAX_POINTS:
        progress.theory_points = Constants.TOPIC_THEORY_MAX_POINTS
    else:
        progress.theory_points += points
    progress.save()


def add_practice_points(progress: Progress, points: float):
    """Добавляет баллы в прогресс пользователя по практике."""
    if progress.practice_points + points > Constants.TOPIC_PRACTICE_MAX_POINTS:
        progress.practice_points = Constants.TOPIC_PRACTICE_MAX_POINTS
    else:
        progress.practice_points += points
    progress.save()
