from django.contrib.auth.models import User

from algorithm.models import Progress, UserAnswer
from config.settings import Constants
from courses.models import (Semester, Problem, Difficulty,
                            THEORY_TYPES, PRACTICE_TYPES)

POINTS_BY_DIFFICULTY = {
    Difficulty.EASY.value: Constants.POINTS_EASY,
    Difficulty.NORMAL.value: Constants.POINTS_NORMAL,
    Difficulty.HARD.value: Constants.POINTS_HARD,
}

DIFFICULTY_TO_POINTS_THRESHOLD = {
    Difficulty.EASY.value: Constants.TOPIC_THRESHOLD_LOW,
    Difficulty.NORMAL.value: Constants.TOPIC_THRESHOLD_MEDIUM,
    Difficulty.HARD.value: Constants.TOPIC_THEORY_MAX_POINTS + Constants.TOPIC_PRACTICE_MAX_POINTS,
}


def add_points_for_problem(user: User, semester: Semester, problem: Problem, coefficient: float):
    """Добавляет баллы во все темы задания."""
    points = coefficient * POINTS_BY_DIFFICULTY[problem.difficulty]
    sub_topic_points = coefficient * points * Constants.SUB_TOPIC_POINTS_COEFFICIENT
    progress = Progress.objects.filter(user=user, semester=semester, topic=problem.main_topic).first()
    add_points_to_main_topic(progress, problem, points)
    for topic in problem.sub_topics.all():
        progress = Progress.objects.filter(user=user, semester=semester, topic=topic).first()
        add_points_to_sub_topic(progress, problem, sub_topic_points)


def add_points_to_main_topic(progress: Progress, problem: Problem, points: float):
    """Добавляет баллы в тему задания не превышая установленного порога."""
    points_threshold = DIFFICULTY_TO_POINTS_THRESHOLD[problem.difficulty]
    if progress.points >= points_threshold:
        return
    elif progress.points + points >= points_threshold:
        points = points_threshold - progress.points
        add_points_to_topic(progress, problem, points)
    else:
        add_points_to_topic(progress, problem, points)


def add_points_to_sub_topic(progress: Progress, problem: Problem, points: float):
    """Добавляет баллы в подтему задания не превышая установленного порога."""
    if progress.points >= Constants.TOPIC_THRESHOLD_MEDIUM:
        return
    elif progress.points + points >= Constants.TOPIC_THRESHOLD_MEDIUM:
        points = Constants.TOPIC_THRESHOLD_MEDIUM - progress.points
        add_points_to_topic(progress, problem, points)
    else:
        add_points_to_topic(progress, problem, points)


def add_points_to_topic(progress: Progress, problem: Problem, points: float):
    """Добавляет баллы в тему задания."""
    if problem.type in THEORY_TYPES:
        add_theory_points(progress, points)
    elif problem.type in PRACTICE_TYPES:
        add_practice_points(progress, points)
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


def add_placement_points_for_problem(progress: Progress, user_answer: UserAnswer):
    """Добавляет баллы во все темы задания с учетом коэффициента калибровки."""
    coefficient = user_answer.coefficient * Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_POINTS_COEFFICIENT
    add_points_for_problem(progress.user, progress.semester, user_answer.problem, coefficient)
