from dataclasses import dataclass

from django.db.models import QuerySet, Q

from algorithm.models import UserCurrentProgress, UserAnswer
from .utils import (is_current_topic_in_progress, increase_difficulty,
                    decrease_difficulty, get_theory_threshold_low)
from courses.models import Problem, Difficulty, THEORY_TYPES


@dataclass
class TheorySelector:

    @property
    def problems(self) -> QuerySet[Problem]:
        """Возвращает теоретические задания."""
        return Problem.objects.filter(type__in=THEORY_TYPES)

    def next(self, u: UserCurrentProgress) -> Problem:
        """Возвращает теоретическое задание по текущей теме пользователя."""
        if u.progress.theory.is_completed():
            raise NotImplementedError('Тест по теории завершен.')
        if not is_current_topic_in_progress(u, THEORY_TYPES):
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
            problem__main_topic=u.progress.topic,
            problem__type__in=THEORY_TYPES
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
            Q(sub_topics__progress__user=u.user) and (
                        Q(sub_topics__theoryprogress__points__gte=threshold_low) or Q(sub_topics__isnull=True)),
            main_topic=u.progress.topic,
            difficulty__lte=max_difficulty,
        ).order_by('-difficulty')
        return problems
