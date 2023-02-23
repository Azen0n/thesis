from dataclasses import dataclass

from django.contrib.auth.models import User

from algorithm.models import (Progress, UserWeakestLinkState, WeakestLinkState,
                              WeakestLinkProblem)
from courses.models import Problem, Semester
from .utils import filter_theory_problems, filter_practice_problems
from .weakest_link import start_weakest_link_when_ready


@dataclass
class ProblemSelector:

    def next_theory_problem(self, progress: Progress) -> Problem:
        """Возвращает следующее теоретическое задание по текущей теме студента."""
        if progress.is_theory_completed():
            raise NotImplementedError('Тест по теории завершен.')
        problem = filter_theory_problems(progress).first()
        if problem is None:
            raise NotImplementedError('Доступных теоретических заданий нет.')
        return problem

    def next_practice_problem(self, user: User, semester: Semester) -> Problem:
        """Возвращает следующее практическое задание по текущей теме студента."""
        user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester).state
        if user_weakest_link_state == WeakestLinkState.IN_PROGRESS:
            return WeakestLinkProblem.objects.filter(user=user, semester=semester,
                                                     is_solved__isnull=True).first()
        if user_weakest_link_state == WeakestLinkState.DONE:
            raise NotImplementedError('Что-то пошло не так с поиском слабого звена.')
        start_weakest_link_when_ready(user, semester)
        problem = filter_practice_problems(user, semester).first()
        if problem is None:
            raise NotImplementedError('Доступных практических заданий нет.')
        return problem
