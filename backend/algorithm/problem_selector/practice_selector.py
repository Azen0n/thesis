from dataclasses import dataclass

from django.db.models import QuerySet, Q

from algorithm.models import UserCurrentProgress, UserAnswer
from algorithm.problem_selector.utils import (
    get_theory_threshold_low, is_current_topic_in_progress,
    change_practice_difficulty, max_practice_difficulty
)
from courses.models import Problem, Difficulty, PRACTICE_TYPES


@dataclass
class PracticeSelector:

    @property
    def problems(self) -> QuerySet[Problem]:
        """Возвращает теоретические задания."""
        return Problem.objects.filter(type__in=PRACTICE_TYPES)

    def next(self, u: UserCurrentProgress) -> Problem:
        """Возвращает практическое задание по текущей теме пользователя."""
        if not u.progress.theory.is_low_reached():
            raise NotImplementedError('Тест по теории не завершен.')
        if u.progress.practice.is_completed():
            raise NotImplementedError('Набран максимальный балл'
                                      ' по практическим заданиям.')
        if not is_current_topic_in_progress(u, PRACTICE_TYPES):
            return self.first_problem(u)
        return self.next_problem(u)

    def first_problem(self, u: UserCurrentProgress) -> Problem:
        """Возвращает первое практическое задание по текущей теме пользователя."""
        max_difficulty = max_practice_difficulty(u)
        problems = self.filter_problems(u, max_difficulty)
        if not problems:
            raise NotImplementedError('Доступных заданий нет.')
        return problems.first()

    def next_problem(self, u: UserCurrentProgress) -> Problem:
        """Возвращает следующее практическое задание по текущей теме пользователя."""
        last_answer = UserAnswer.objects.filter(
            user=u.user,
            problem__main_topic=u.progress.topic,
            problem__type__in=PRACTICE_TYPES
        ).order_by('-created_at').first()
        if last_answer.is_solved:
            difficulty = change_practice_difficulty(u, last_answer.problem.difficulty)
        else:
            raise NotImplementedError('Запускается режим поиска слабого звена.')
        problems = self.filter_problems(u, difficulty)
        if not problems:
            raise NotImplementedError('Доступных заданий нет.')
        return problems.first()

    def filter_problems(self, u: UserCurrentProgress,
                        max_difficulty: Difficulty) -> QuerySet[Problem]:
        """Возвращает практические задания, доступные для текущего пользователя
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
