from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generator


class Style(Enum):
    TOPIC_BASED = 1
    THEORY_FIRST = 2


@dataclass
class Pattern:
    """Паттерн прохождения курса студентом.
    target_points_coefficient - доля баллов от 0 до 1, к которому стремится студент.
    style - стиль прохождения курса:
        - TOPIC_BASED - Прохождение теории и практики чередуется: сначала закрывается теория
        по теме, затем практика по ней.
        - THEORY_FIRST - Сначала проходится теория по всем темам, затем практика.
    generator - генератор, возвращающий ответ на задание по формуле.
    """
    target_points_coefficient: float
    style: Style
    generator: Callable[[], Generator[bool, None, None]]

    def __post_init__(self):
        self.probability_generator = self.generator()

    def is_next_problem_solved(self) -> bool:
        return next(self.probability_generator)
