import random
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generator

import math

from algorithm.models import TargetPoints


class Style(Enum):
    MODULE_BASED = 1
    THEORY_FIRST = 2


@dataclass
class Pattern:
    """Паттерн прохождения курса студентом.
    target_points - количество баллов, к которым стремится студент.
    style - стиль прохождения курса:
        - MODULE_BASED - Прохождение курса по модулям: сначала закрывается теория
        по всем темам модуля, затем практика по нему.
        - THEORY_FIRST - Сначала проходится теория по всем темам, затем практика.
    generator - генератор, возвращающий ответ на задание по формуле.
    """
    target_points: TargetPoints
    style: Style
    generator: Callable[[], Generator[bool, None, None]]

    def __post_init__(self):
        self.probability_generator = self.generator()

    def is_next_problem_solved(self) -> bool:
        return next(self.probability_generator)


def motivation_decay_generator() -> Generator[bool, None, None]:
    """Паттерн поведения студента «снижение мотивации со временем»,
    когда студенты начинают курс с большим энтузиазмом и высокой мотивацией,
    но по мере продвижения по курсу и накопления материала их интерес
    начинает уменьшаться.
    """
    number_of_problems_solved = 0
    while True:
        if number_of_problems_solved < 45:
            chance = 0.99
        elif number_of_problems_solved < 90:
            chance = 0.89
        elif number_of_problems_solved < 135:
            chance = 0.79
        else:
            chance = 0.69
        yield random.uniform(0, 1) < chance
        number_of_problems_solved += 1


def motivation_spikes_generator() -> Generator[bool, None, None]:
    """Паттерн поведения студента «периодические всплески мотивации»,
    когда студенты проявляют более высокую активность и энтузиазм периодически.
    """
    i = 0
    while True:
        yield random.uniform(0, 1) < 0.63 + (abs(math.sin(i / 20)) / 2.5) - 0.05
        i += 1


def falling_behind_generator() -> Generator[bool, None, None]:
    """Паттерн поведения студента «отставание», когда студенты начинают
    отставать от графика курса, не успевают выполнить задания вовремя,
    и это может приводить к дополнительному стрессу и ухудшению мотивации.
    """
    i = -100
    while True:
        yield random.uniform(0, 1) < 0.54 + abs(0.6 + (i / 30) ** 2) / 25
        i += 1


def excessive_perfectionism_generator() -> Generator[bool, None, None]:
    """Паттерн поведения студента «излишний перфекционизм»,
    когда студенты тратят слишком много времени на изучение
    отдельных тем и деталей.
    """
    while True:
        yield random.uniform(0, 1) < 0.95
