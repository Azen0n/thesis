from __future__ import annotations
from dataclasses import dataclass

from datatypes import TheoryProblem, User, Difficulty


@dataclass
class TheorySelector:
    problems: list[TheoryProblem]

    def next(self, user: User) -> TheoryProblem:
        """Подбирает следующее задание из теста по теории."""
        if user.current_topic.theory.is_completed():
            raise NotImplementedError('Тест по теории завершен.')
        if not user.theory.is_current_topic_in_progress():
            return self.first_problem(user)
        return self.next_problem(user)

    def first_problem(self, user: User) -> TheoryProblem:
        """Возвращает первое задание с учетом предпочтения сложности
        пользователя.
        """
        problems = self.available_problems(user, max_difficulty=user.difficulty_preference)
        problems = self.sort_problems_by_difficulty(problems, reverse=True)
        try:
            return problems[0]
        except (StopIteration, IndexError):
            raise NotImplementedError('Доступных заданий нет.')

    def next_problem(self, user: User) -> TheoryProblem:
        """Возвращает задание с учетом результата решения предыдущего."""
        last_attempt = user.theory.attempts_of_topic(user.current_topic.topic)[-1]
        if last_attempt.is_solved:
            difficulty = last_attempt.problem.difficulty.increase()
        else:
            difficulty = last_attempt.problem.difficulty.decrease()
        problems = self.available_problems(user, max_difficulty=difficulty)
        problems = self.sort_problems_by_difficulty(problems, reverse=True)
        if not problems:
            raise NotImplementedError('Нет заданий с подходящей сложностью.')
        return problems[0]

    def available_problems(self, user: User,
                           max_difficulty: Difficulty = None,
                           difficulty: Difficulty = None) -> list[TheoryProblem]:
        """Возвращает список заданий, доступных в активной теме пользователя.

        max_difficulty — все задания со сложностью равной max_difficulty и ниже.
        difficulty — все задания со сложностью равной difficulty.
        """
        problems = [problem for problem in self.problems
                    if problem.is_available_for(user)
                    and not user.theory.was_attempt_on_problem(problem)]
        if max_difficulty is not None:
            problems = [problem for problem in problems
                        if problem.difficulty.value <= max_difficulty.value]
        if difficulty is not None:
            problems = [problem for problem in problems
                        if problem.difficulty == difficulty]
        return problems

    def sort_problems_by_difficulty(self, problems: list[TheoryProblem],
                                    reverse: bool = False) -> list[TheoryProblem]:
        """Возвращает список заданий, отсортированный по сложности
        в порядке возрастания.
        """
        return sorted(problems, key=lambda x: x.difficulty.value, reverse=reverse)
