import math

from django.db.models import QuerySet, Q

from algorithm.models import UserCurrentProgress
from courses.models import Course, Difficulty, Type, Problem


def find_problem(u: UserCurrentProgress, types: list[Type]) -> Problem:
    """Возвращает наиболее сложное задание из всех доступных заданий
    с использованием логистической модели Раша.
    """
    difficulty = get_suitable_problem_difficulty(u)
    problem = filter_problems(u, difficulty, types).first()
    return problem


def filter_problems(u: UserCurrentProgress,
                    max_difficulty: Difficulty, types: list[Type]) -> QuerySet[Problem]:
    """Возвращает теоретические задания, доступные для текущего пользователя
    в порядке убывания сложности.
    """
    threshold_low = get_theory_threshold_low(u.progress.topic.module.course)
    problems = Problem.objects.filter(
        ~Q(useranswer__user=u.user),
        Q(sub_topics__progress__user=u.user) and (
                Q(sub_topics__theoryprogress__points__gte=threshold_low) or Q(sub_topics__isnull=True)),
        type__in=types,
        main_topic=u.progress.topic,
        difficulty__lte=max_difficulty,
    ).order_by('-difficulty')
    return problems


def get_theory_threshold_low(course: Course) -> float:
    """Возвращает минимальное количество баллов, необходимое для завершения
    теории по теме.
    """
    topic_max_points = course.topic_max_points
    threshold_low = course.topic_threshold_low
    low = course.topic_theory_max_points * (threshold_low / topic_max_points)
    return low


def get_suitable_problem_difficulty(u: UserCurrentProgress) -> Difficulty:
    """Возвращает уровень сложности теоретического задания,
    подходящий для текущей темы студента.
    """
    probability = u.semester.course.algorithm_suitable_difficulty_probability
    if correct_answer_probability(u, Difficulty.HARD) >= probability:
        return Difficulty.HARD
    if correct_answer_probability(u, Difficulty.NORMAL) >= probability:
        return Difficulty.NORMAL
    return Difficulty.EASY


def correct_answer_probability(u: UserCurrentProgress, difficulty: Difficulty) -> float:
    """Рассчитывает вероятность правильного ответа на задание с указанной сложностью."""
    coefficient = {
        Difficulty.EASY: u.semester.course.algorithm_difficulty_coefficient_easy,
        Difficulty.NORMAL: u.semester.course.algorithm_difficulty_coefficient_normal,
        Difficulty.HARD: u.semester.course.algorithm_difficulty_coefficient_hard
    }
    return 1 / (1 + math.exp(-(u.progress.skill_level - coefficient[difficulty])))
