import math
from django.contrib.auth.models import User
from django.db.models import QuerySet

from algorithm.models import Progress
from answers.points_management import DIFFICULTY_TO_POINTS_THRESHOLD
from config.settings import Constants
from courses.models import Semester, Problem, Difficulty, Type, THEORY_TYPES

POINTS_BY_DIFFICULTY = {
    Difficulty.EASY.value: Constants.POINTS_EASY,
    Difficulty.NORMAL.value: Constants.POINTS_NORMAL,
    Difficulty.HARD.value: Constants.POINTS_HARD,
}


def get_problems_with_max_value(user: User, semester: Semester, problems: QuerySet[Problem]) -> list[Problem]:
    """Возвращает задания, отсортированные в порядке убывания их ценности."""
    problems_with_value = []
    for problem in problems:
        value = calculate_problem_value(user, semester, problem)
        problems_with_value.append((problem, value))
    problems_with_value.sort(key=lambda x: x[1])
    return [problem for problem, _ in problems_with_value]


def calculate_problem_value(user: User, semester: Semester, problem: Problem) -> float:
    """Рассчитывает "стоимость" задания, основываясь на прогрессе тем этого
    задания, уровне знаний и времени на решение.
    """
    progress = Progress.objects.get(user=user, semester=semester, topic=problem.main_topic)
    skill_level_coefficient = Constants.AVERAGE_SKILL_LEVEL / progress.skill_level
    weighted_time_to_solve = problem.time_to_solve_in_seconds * skill_level_coefficient
    points = calculate_points_if_problem_solved_correctly(progress, problem)
    return math.inf if points == 0 else weighted_time_to_solve / (points * threshold_coefficient(progress))


def threshold_coefficient(progress: Progress) -> float:
    """Возвращает коэффициент ценности темы в зависимости от количества баллов."""
    if progress.points < Constants.TOPIC_THRESHOLD_LOW:
        return Constants.TOPIC_THRESHOLD_LOW_COEFFICIENT
    if progress.points < Constants.TOPIC_THRESHOLD_MEDIUM:
        return Constants.TOPIC_THRESHOLD_MEDIUM_COEFFICIENT
    return Constants.TOPIC_THRESHOLD_HIGH_COEFFICIENT


def calculate_points_if_problem_solved_correctly(progress: Progress, problem: Problem) -> float:
    """Возвращает общее количество баллов, которое получит пользователь при
    правильном решении задания.
    """
    sub_topics_progresses = Progress.objects.filter(
        user=progress.user,
        semester=progress.semester,
        topic__in=problem.sub_topics.all()
    )
    main_topic_points = POINTS_BY_DIFFICULTY[problem.difficulty]
    sub_topic_points = POINTS_BY_DIFFICULTY[problem.difficulty] * Constants.SUB_TOPIC_POINTS_COEFFICIENT
    total_points = main_topic_points_if_problem_solved_correctly(progress, main_topic_points, problem)
    for sub_topic_progress in sub_topics_progresses:
        total_points += sub_topic_points_if_problem_solved_correctly(sub_topic_progress,
                                                                     sub_topic_points, problem)
    return total_points


def main_topic_points_if_problem_solved_correctly(progress: Progress,
                                                  points: float,
                                                  problem: Problem) -> float:
    """Возвращает количество баллов, которое получит пользователь по основной теме,
    если решит теоретическое или практическое задание правильно.
    """
    points_threshold = DIFFICULTY_TO_POINTS_THRESHOLD[problem.difficulty]
    if progress.points >= points_threshold:
        return 0
    elif progress.points + points >= points_threshold:
        points = points_threshold - progress.points
    return points_if_problem_solved_correctly(progress, points, problem)


def sub_topic_points_if_problem_solved_correctly(progress: Progress,
                                                 points: float,
                                                 problem: Problem) -> float:
    """Возвращает количество баллов, которое получит пользователь по подтеме,
    если решит теоретическое или практическое задание правильно.
    """
    if progress.points >= Constants.TOPIC_THRESHOLD_MEDIUM:
        return 0
    elif progress.points + points >= Constants.TOPIC_THRESHOLD_MEDIUM:
        points = Constants.TOPIC_THRESHOLD_MEDIUM - progress.points
    return points_if_problem_solved_correctly(progress, points, problem)


def points_if_problem_solved_correctly(progress: Progress, points: float, problem: Problem) -> float:
    """Возвращает количество баллов, которое получит пользователь,
    если решит теоретическое или практическое задание правильно.
    """
    current_points, max_points = get_points_by_problem_type(progress, Type(problem.type))
    if current_points >= max_points:
        return 0
    elif current_points + points > max_points:
        return max_points - current_points
    else:
        return points


def get_points_by_problem_type(progress: Progress, problem_type: Type) -> tuple[float, float]:
    """Возвращает текущее количество баллов и максимально доступное
    в зависимости от типа задания.
    """
    if problem_type in THEORY_TYPES:
        current_points = progress.theory_points
        max_points = Constants.TOPIC_THEORY_MAX_POINTS
    else:
        current_points = progress.practice_points
        max_points = Constants.TOPIC_PRACTICE_MAX_POINTS
    return current_points, max_points
