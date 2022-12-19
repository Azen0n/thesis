from __future__ import annotations
from dataclasses import dataclass

from datatypes import PracticeProblem, User, Difficulty, Attempt, Topic

MAX_NUMBER_OF_PROBLEMS_PER_SUB_TOPIC = 2


@dataclass
class PracticeSelector:
    problems: list[PracticeProblem]

    def next(self, user: User) -> PracticeProblem:
        """Подбирает следующее практическое задание."""
        if not user.current_topic.theory.is_low_reached():
            raise NotImplementedError('Тест по теории не завершен.')
        if user.current_topic.practice.is_completed():
            raise NotImplementedError('Набран максимальный балл по'
                                      ' практическим заданиям.')
        if not user.practice.is_current_topic_in_progress():
            return self.first_problem(user)
        return self.next_problem(user)

    def first_problem(self, user: User) -> PracticeProblem:
        """Возвращает первое практическое задание по теме."""
        max_difficulty = user.current_topic.max_difficulty()
        problems = self.available_problems(user, max_difficulty)
        problems = self.sort_problems_by_difficulty(problems, reverse=True)
        try:
            return problems[0]
        except IndexError:
            raise NotImplementedError('Доступных заданий нет.')

    def next_problem(self, user: User) -> PracticeProblem:
        """Возвращает задание с учетом результата решения предыдущего."""
        problem = self.check_for_weakest_link(user)
        if problem is not None:
            return problem
        last_attempt = user.practice.attempts_of_topic(user.current_topic.topic)[-1]
        if last_attempt.is_solved:
            difficulty = self.change_difficulty(user, last_attempt)
        else:
            problem = self.find_weakest_link(user, last_attempt)
            if problem:
                return problem
            difficulty = last_attempt.problem.difficulty.decrease()
        problems = self.available_problems(user, max_difficulty=difficulty)
        problems = self.sort_problems_by_difficulty(problems, reverse=True)
        if not problems:
            raise NotImplementedError('Нет заданий с подходящей сложностью.')
        return problems[0]

    def check_for_weakest_link(self, user: User) -> PracticeProblem | None:
        """Проверяет, нужно ли обрабатывать очередь поиска слабого звена."""
        if user.current_topic.practice.is_time_to_throw_weakest_link:
            self.update_weakest_link(user)
            self.throw_weakest_link(user)
        if user.current_topic.practice.weakest_link_queue:
            self.update_weakest_link(user)
            return self.first_problem_from_weakest_link_queue(user)
        return None

    def throw_weakest_link(self, user: User):
        """Поиск слабого звена завершен."""
        user.current_topic.practice.is_time_to_throw_weakest_link = False
        weakest_links = user.current_topic.practice.weakest_links
        user.current_topic.practice.weakest_links = set()
        raise NotImplementedError(f'Обнаружены проблемные темы: '
                                  f'{weakest_links}!')

    def change_difficulty(self, user: User,
                          last_attempt: Attempt) -> Difficulty:
        """На основе последней попытки пользователя (успешной) повышает
        сложность или оставляет ее на том же уровне."""
        max_difficulty = user.current_topic.max_difficulty()
        difficulty = last_attempt.problem.difficulty.increase()
        if difficulty.value > max_difficulty.value:
            difficulty = max_difficulty
        return difficulty

    def find_weakest_link(self, user: User,
                          last_attempt: Attempt) -> PracticeProblem | None:
        """Если на практическое задание дан неверный ответ, алгоритм подбирает
        задания со смежными темами, чтобы найти ту, которая могла стать
        причиной этого неверного ответа.

        При первом неверном ответе подбирается несколько заданий и помещаются
        в очередь, возвращается первое задание из очереди.
        """
        practice = user.current_topic.practice
        if practice.weakest_link_queue:
            return self.first_problem_from_weakest_link_queue(user)
        sub_topics = last_attempt.problem.sub_topics
        problems = self.available_problems(
            user, max_difficulty=user.current_topic.max_difficulty()
        )
        problems = self.problems_to_find_weakest_link(sub_topics,
                                                      problems)
        if not problems:
            return None
        problems = self.sort_problems_by_difficulty(problems, reverse=True)
        practice.weakest_links = sub_topics
        practice.weakest_link_queue = problems
        return self.first_problem_from_weakest_link_queue(user)

    def first_problem_from_weakest_link_queue(self, user: User) -> PracticeProblem:
        """Возвращает первое практическое задание из очереди заданий
        на определение проблемной темы. Если очередь заканчивается,
        устанавливает флаг на определение темы.
        """
        practice = user.current_topic.practice
        if not practice.weakest_link_queue:
            self.throw_weakest_link(user)
        problem = practice.weakest_link_queue.pop(0)
        if not practice.weakest_link_queue:
            practice.is_time_to_throw_weakest_link = True
        return problem

    def problems_to_find_weakest_link(self, sub_topics: set[Topic],
                                      problems: list[PracticeProblem]) -> list[PracticeProblem]:
        """Возвращает список практических заданий, подтемы которых отличаются
        на одну тему."""
        if len(sub_topics) == 1:
            suitable_problems = self.get_problems_with_equal_sub_topics(sub_topics, problems)
        else:
            suitable_problems = self.get_problems_with_difference_in_one_sub_topic(sub_topics, problems)

        problem_counter = {topic: 0 for topic in sub_topics}
        problems = []
        for topic in sub_topics:
            for problem in suitable_problems:
                if topic in problem.sub_topics and problem not in problems:
                    problems.append(problem)
                    problem_counter[topic] += 1
                if problem_counter[topic] == MAX_NUMBER_OF_PROBLEMS_PER_SUB_TOPIC:
                    break
        return problems

    def get_problems_with_equal_sub_topics(self, sub_topics: set[Topic],
                                           problems: list[PracticeProblem]) -> list[PracticeProblem]:
        problems_with_equal_sub_topics = []
        for problem in problems:
            if sub_topics == problem.sub_topics:
                problems_with_equal_sub_topics.append(problem)
        return problems_with_equal_sub_topics

    def get_problems_with_difference_in_one_sub_topic(self, sub_topics: set[Topic],
                                                      problems: list[PracticeProblem]) -> list[PracticeProblem]:
        problems_with_difference_in_one_sub_topic = []
        for problem in problems:
            if len(sub_topics.difference(problem.sub_topics)) == 1:
                problems_with_difference_in_one_sub_topic.append(problem)
        return problems_with_difference_in_one_sub_topic

    def update_weakest_link(self, user: User):
        """На основе последней попытки пользователя обновляет
        список проблемных тем.
        """
        practice = user.current_topic.practice
        last_attempt = user.practice.attempts[-1]
        weakest_links = practice.weakest_links
        topic = next(iter(last_attempt.problem.sub_topics.intersection(weakest_links)))
        if last_attempt.is_solved:
            weakest_links.remove(topic)
            practice.remove_weakest_link_from_queue(topic)
            if not practice.weakest_link_queue:
                practice.is_time_to_throw_weakest_link = True

    def available_problems(self, user: User,
                           max_difficulty: Difficulty = None,
                           difficulty: Difficulty = None) -> list[PracticeProblem]:
        """Возвращает список заданий, доступных в активной теме пользователя.

        max_difficulty — все задания со сложностью равной max_difficulty и ниже.
        difficulty — все задания со сложностью равной difficulty.
        """
        problems = [problem for problem in self.problems
                    if problem.is_available_for(user)
                    and not user.practice.was_attempt_on_problem(problem)]
        if max_difficulty is not None:
            problems = [problem for problem in problems
                        if problem.difficulty.value <= max_difficulty.value]
        if difficulty is not None:
            problems = [problem for problem in problems
                        if problem.difficulty == difficulty]
        return problems

    def sort_problems_by_difficulty(self, problems: list[PracticeProblem],
                                    reverse: bool = False) -> list[PracticeProblem]:
        """Возвращает список заданий, отсортированный по сложности
        в порядке возрастания.
        """
        return sorted(problems,
                      key=lambda x: x.difficulty.value,
                      reverse=reverse)
