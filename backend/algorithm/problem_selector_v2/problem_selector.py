from dataclasses import dataclass

from algorithm.models import UserCurrentProgress
from courses.models import Problem
from .theory_selector import TheorySelector


@dataclass
class ProblemSelector:
    theory_selector: TheorySelector = None

    def __post_init__(self):
        self.theory_selector = TheorySelector()

    def next_theory_problem(self, u: UserCurrentProgress) -> Problem:
        return self.theory_selector.next(u)
