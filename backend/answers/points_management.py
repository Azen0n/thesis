from django.contrib.auth.models import User

from algorithm.models import Progress
from config.settings import Constants
from courses.models import (Semester, Problem, Difficulty, Topic,
                            THEORY_TYPES, PRACTICE_TYPES)

POINTS_BY_DIFFICULTY = {
    Difficulty.EASY.value: Constants.POINTS_EASY,
    Difficulty.NORMAL.value: Constants.POINTS_NORMAL,
    Difficulty.HARD.value: Constants.POINTS_HARD,
}


def add_points_for_problem(user: User, semester: Semester, problem: Problem, coefficient: float):
    """Добавляет баллы во все темы задания."""
    points = coefficient * POINTS_BY_DIFFICULTY[problem.difficulty]
    sub_topic_points = coefficient * points * Constants.SUB_TOPIC_POINTS_COEFFICIENT
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
