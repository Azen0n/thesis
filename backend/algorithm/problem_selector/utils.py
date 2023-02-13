from algorithm.models import UserCurrentProgress, UserAnswer
from courses.models import Course, Difficulty, Type, PRACTICE_TYPES


def get_theory_threshold_low(course: Course) -> float:
    """Возвращает минимальное количество баллов, необходимое для завершения
    теории по теме.
    """
    topic_max_points = course.topic_max_points
    threshold_low = course.topic_threshold_low
    low = course.topic_theory_max_points * (threshold_low / topic_max_points)
    return low


def is_current_topic_in_progress(u: UserCurrentProgress, types: list[Type]) -> bool:
    """Проверка на наличие ответов от пользователя по текущей теме."""
    return UserAnswer.objects.filter(
        user=u.user,
        problem__main_topic=u.progress.topic,
        problem__type__in=types,
    ).first() is not None


def increase_difficulty(value: int) -> Difficulty:
    """Повышает сложность на один уровень."""
    try:
        return Difficulty(value + 1)
    except ValueError:
        return Difficulty(value)


def decrease_difficulty(value: int) -> Difficulty:
    """Понижает сложность на один уровень."""
    try:
        return Difficulty(value - 1)
    except ValueError:
        return Difficulty(value)


def max_practice_difficulty(u: UserCurrentProgress) -> Difficulty:
    """Возвращает максимальную доступную сложность практических заданий
    по текущей теме пользователя.
    """
    easy_problem_count, normal_problem_count = [
        count_solved_practice_problems(u, difficulty)
        for difficulty in [Difficulty.EASY, Difficulty.NORMAL]
    ]
    course = u.progress.topic.module.course
    if u.progress.theory.is_high_reached():
        return Difficulty.HARD
    if normal_problem_count >= course.difficulty_threshold_hard:
        return Difficulty.HARD
    if u.progress.theory.is_medium_reached():
        return Difficulty.NORMAL
    if easy_problem_count >= course.difficulty_threshold_normal:
        return Difficulty.NORMAL
    if u.progress.theory.is_low_reached():
        return Difficulty.EASY
    raise NotImplementedError('Тест по теории не завершен.')


def count_solved_practice_problems(u: UserCurrentProgress,
                                   difficulty: Difficulty) -> int:
    """Возвращает количество решенных практических заданий по текущей теме
    пользователя с указанной сложностью.
    """
    return UserAnswer.objects.filter(
        user=u.user,
        problem__main_topic=u.progress.topic,
        problem__type__in=PRACTICE_TYPES,
        problem__difficulty=difficulty,
        is_solved=True
    ).count()


def change_practice_difficulty(u: UserCurrentProgress,
                               difficulty: Difficulty) -> Difficulty:
    """Повышает сложность практического задания или оставляет ее на том же уровне."""
    max_difficulty = max_practice_difficulty(u)
    difficulty = increase_difficulty(difficulty)
    return difficulty if difficulty.value <= max_difficulty.value else max_difficulty
