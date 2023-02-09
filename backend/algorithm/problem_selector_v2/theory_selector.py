from dataclasses import dataclass

from django.db.models import QuerySet, Q

from algorithm.models import UserCurrentProgress, UserAnswer
from courses.models import Problem, Type, Course, Difficulty


@dataclass
class TheorySelector:

    @property
    def problems(self) -> QuerySet[Problem]:
        """Возвращает теоретические задания."""
        return Problem.objects.filter(type__in=[
            Type.MULTIPLE_CHOICE_RADIO,
            Type.MULTIPLE_CHOICE_CHECKBOX,
            Type.FILL_IN_SINGLE_BLANK,
        ])

    def next(self, u: UserCurrentProgress) -> Problem:
        """Возвращает теоретическое задание по текущей теме пользователя."""
        if u.progress.theory.is_completed():
            raise NotImplementedError('Тест по теории завершен.')
        if is_current_topic_in_progress(u):
            return self.first_problem(u)
        return self.next_problem(u)

    def first_problem(self, u: UserCurrentProgress) -> Problem:
        """Возвращает первое задание по текущей теме пользователя."""
        problems = self.filter_problems(u, max_difficulty=Difficulty.NORMAL)
        if not problems:
            raise NotImplementedError('Доступных заданий нет.')
        return problems.first()

    def next_problem(self, u: UserCurrentProgress) -> Problem:
        """Возвращает следующее задание по текущей теме пользователя."""
        last_answer = UserAnswer.objects.filter(
            user=u.user,
            problem__main_topic=u.progress.topic
        ).order_by('-created_at').first()
        if last_answer.is_solved:
            difficulty = increase_difficulty(last_answer.problem.difficulty)
        else:
            difficulty = decrease_difficulty(last_answer.problem.difficulty)
        problems = self.filter_problems(u, max_difficulty=difficulty)
        if not problems:
            raise NotImplementedError('Доступных заданий нет.')
        return problems.first()

    def filter_problems(self, u: UserCurrentProgress,
                        max_difficulty: Difficulty) -> QuerySet[Problem]:
        """Возвращает теоретические задания, доступные для текущего пользователя
        в порядке убывания сложности.
        """
        threshold_low = get_theory_threshold_low(u.progress.topic.module.course)
        problems = self.problems.filter(
            ~Q(useranswer__user=u.user),
            Q(sub_topics__theoryprogress__points__gte=threshold_low) | Q(sub_topics__isnull=True),
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


def is_current_topic_in_progress(u: UserCurrentProgress) -> bool:
    """Проверка на наличие ответов от пользователя по текущей теме."""
    return UserAnswer.objects.filter(
        user=u.user,
        problem__main_topic=u.progress.topic
    ).first() is None


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
