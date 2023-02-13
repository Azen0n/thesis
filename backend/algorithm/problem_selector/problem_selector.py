from dataclasses import dataclass

from algorithm.models import UserCurrentProgress
from courses.models import Problem
from .practice_selector import PracticeSelector
from .theory_selector import TheorySelector


@dataclass
class ProblemSelector:
    theory_selector: TheorySelector = None
    practice_selector: PracticeSelector = None

    def __post_init__(self):
        self.theory_selector = TheorySelector()
        self.practice_selector = PracticeSelector()

    def next_theory_problem(self, u: UserCurrentProgress) -> Problem:
        return self.theory_selector.next(u)

    def next_practice_problem(self, u: UserCurrentProgress) -> Problem:
        return self.practice_selector.next(u)
