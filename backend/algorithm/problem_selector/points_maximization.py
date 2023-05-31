import logging

from django.contrib.auth.models import User
from django.db.models import QuerySet

from algorithm.models import Progress
from config.settings import Constants
from courses.models import Semester, Problem, Difficulty, Type, THEORY_TYPES

POINTS_BY_DIFFICULTY = {
    Difficulty.EASY.value: Constants.POINTS_EASY,
    Difficulty.NORMAL.value: Constants.POINTS_NORMAL,
    Difficulty.HARD.value: Constants.POINTS_HARD,
}

logger = logging.getLogger(__name__)


def get_problems_with_max_value(user: User, semester: Semester, problems: QuerySet[Problem]) -> list[Problem]:
    """Возвращает задания, отсортированные в порядке убывания их ценности."""
    problems_with_value = []
    for problem in problems:
        value = calculate_problem_value(user, semester, problem)
        problems_with_value.append((problem, value))
    problems_with_value.sort(key=lambda x: x[1])
    for problem, value in problems_with_value[:15]:
        logger.info(f'(   ) {user.username:<10} {problem.title:<25}'
                    f' {problem.difficulty} {problem.time_to_solve_in_seconds:<6}'
                    f' value={value}')
    return [problem for problem, _ in problems_with_value]


def calculate_problem_value(user: User, semester: Semester, problem: Problem) -> float:
    """Рассчитывает "стоимость" задания, основываясь на прогрессе тем этого
    задания, уровне знаний и времени на решение.
    """
    progress = Progress.objects.get(user=user, semester=semester, topic=problem.main_topic)
    skill_level_coefficient = Constants.AVERAGE_SKILL_LEVEL / progress.skill_level
    weighted_time_to_solve = problem.time_to_solve_in_seconds * skill_level_coefficient
    points = calculate_points_if_problem_solved_correctly(progress, problem)
    return weighted_time_to_solve / points


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
    total_points = points_if_problem_solved_correctly(progress, main_topic_points, Type(problem.type))
    for sub_topic_progress in sub_topics_progresses:
        total_points += points_if_problem_solved_correctly(sub_topic_progress,
                                                           sub_topic_points, Type(problem.type))
    return total_points


def points_if_problem_solved_correctly(progress: Progress, points: float, problem_type: Type) -> float:
    """Возвращает количество баллов, которое получит пользователь по теме,
    если решит теоретическое или практическое задание правильно.
    """
    current_points, max_points = get_points_by_problem_type(progress, problem_type)
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
