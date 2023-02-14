from dataclasses import dataclass

from algorithm.models import UserCurrentProgress, UserAnswer
from courses.models import Problem, THEORY_TYPES, PRACTICE_TYPES
from .utils import find_problem


@dataclass
class ProblemSelector:

    def next_theory_problem(self, u: UserCurrentProgress) -> Problem:
        """Возвращает следующее теоретическое задание по текущей теме студента."""
        if u.progress.theory.is_completed():
            raise NotImplementedError('Тест по теории завершен.')
        problem = find_problem(u, THEORY_TYPES)
        if not problem:
            raise NotImplementedError('Доступных заданий нет.')
        return problem

    def next_practice_problem(self, u: UserCurrentProgress) -> Problem:
        """Возвращает следующее практическое задание по текущей теме студента."""
        if not u.progress.theory.is_low_reached():
            raise NotImplementedError('Тест по теории не завершен.')
        if u.progress.practice.is_completed():
            raise NotImplementedError('Набран максимальный балл'
                                      ' по практическим заданиям.')
        last_answer = UserAnswer.objects.filter(
            user=u.user,
            problem__main_topic=u.progress.topic,
            problem__type__in=PRACTICE_TYPES
        ).order_by('-created_at').first()
        if not last_answer.is_solved:
            raise NotImplementedError('Запускается режим поиска слабого звена.')
        problem = find_problem(u, PRACTICE_TYPES)
        if not problem:
            raise NotImplementedError('Доступных заданий нет.')
        return problem
