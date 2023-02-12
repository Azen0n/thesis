from dataclasses import dataclass

from prettytable import PrettyTable

from .datatypes import User, Topic, TheoryProblem, PracticeProblem, Problem
from .practice_selector import PracticeSelector
from .theory_selector import TheorySelector


@dataclass
class ProblemSelector:
    theory_problems: list[TheoryProblem]
    practice_problems: list[PracticeProblem]
    theory_selector: TheorySelector = None
    practice_selector: PracticeSelector = None

    def __post_init__(self):
        self.theory_selector = TheorySelector(self.theory_problems)
        self.practice_selector = PracticeSelector(self.practice_problems)

    def next_theory_problem(self, user: User) -> Problem:
        return self.theory_selector.next(user)

    def next_practice_problem(self, user: User) -> Problem:
        return self.practice_selector.next(user)

    def __str__(self):
        users = ''
        for user in self.users:
            users += f' - {user}\n'

        topics = ''
        for topic in self.topics:
            topics += f' - {topic}\n'

        theory_problems = self.__problems_list_to_table(self.theory_problems)
        practice_problems = self.__problems_list_to_table(self.practice_problems)

        return (f'users:\n{users}\n'
                f'topics:\n{topics}\n'
                f'theory problems:\n{theory_problems}\n'
                f'practice problems:\n{practice_problems}')

    def __problems_list_to_table(self, problems: list[Problem]) -> str:
        table = PrettyTable()
        table.field_names = ['id', 'difficulty', 'main topic', 'sub topics']

        for problem in problems:
            table.add_row([problem.id, problem.difficulty, problem.main_topic,
                           ", ".join([topic.title for topic in problem.sub_topics])])
        return str(table)
