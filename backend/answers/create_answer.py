from algorithm.models import (UserCurrentProgress, UserAnswer,
                              Progress, AbstractProgress)
from .models import Answer
from courses.models import (Problem, THEORY_TYPES, PRACTICE_TYPES,
                            Difficulty, Topic)


def create_user_answer(u: UserCurrentProgress, problem: Problem,
                       is_solved: bool):
    """Создает ответ пользователя на задание и добавляет баллы в его
    главную тему и подтемы.
    """
    user_answer = UserAnswer.objects.create(
        user=u.user,
        semester=u.semester,
        problem=problem,
        is_solved=is_solved,
        answer=Answer.objects.create()
    )
    change_user_skill_level(u, user_answer)
    points_by_difficulty = {
        Difficulty.EASY: u.semester.course.points_easy,
        Difficulty.NORMAL: u.semester.course.points_normal,
        Difficulty.HARD: u.semester.course.points_hard,
    }
    if is_solved:
        points = points_by_difficulty[Difficulty(problem.difficulty)]
        sub_topic_points = points * u.semester.course.sub_topic_points_coefficient
        add_points_to_topic(u, problem.main_topic, problem, points)
        for topic in problem.sub_topics.all():
            add_points_to_topic(u, topic, problem, sub_topic_points)


def change_user_skill_level(u: UserCurrentProgress, user_answer: UserAnswer):
    """Изменяет уровень знаний пользователя по текущей теме в зависимости от
    правильности ответа на задание."""
    placement_coefficient = get_skill_level_placement_coefficient(u)
    if user_answer.is_solved:
        u.progress.skill_level += placement_coefficient * u.semester.course.algorithm_correct_answer_bonus
    else:
        u.progress.skill_level -= placement_coefficient * u.semester.course.algorithm_wrong_answer_penalty
    u.progress.save()


def get_skill_level_placement_coefficient(u: UserCurrentProgress) -> float:
    """Калибровка уровня знаний студента. За первые несколько ответов
    пользователь получает больший прирост.

    Возвращает коэффициент прироста.
    """
    number_of_answered_problems = UserAnswer.objects.filter(
        user=u.user,
        problem__main_topic=u.progress.topic
    ).order_by('-created_at').count()
    placement_answers = u.semester.course.algorithm_skill_level_placement_answers
    if number_of_answered_problems < placement_answers:
        coefficient = placement_answers + 1 - number_of_answered_problems
    else:
        coefficient = 1
    return coefficient


def add_points_to_topic(u: UserCurrentProgress, topic: Topic,
                        problem: Problem, points: float):
    """Добавляет баллы в тему задания."""
    topic_progress = Progress.objects.filter(
        user=u.user,
        semester=u.semester,
        topic=topic
    ).first()
    if topic_progress is None:
        raise ValueError(f'Прогресс пользователя {u.user}'
                         f' по теме {topic} ({topic.id}) не найден.')
    if problem.type in THEORY_TYPES:
        add_points(topic_progress.theory, points)
    elif problem.type in PRACTICE_TYPES:
        add_points(topic_progress.practice, points)
    else:
        raise ValueError(f'Тип {problem.type} задания {problem}'
                         f' не относится к теоретическим или'
                         f' практическим типам.')


def add_points(progress: AbstractProgress, points: float):
    """Добавляет баллы в прогресс пользователя по текущей теме."""
    if progress.points + points > progress.max:
        progress.points = progress.max
    else:
        progress.points = progress.points + points
    progress.save()
