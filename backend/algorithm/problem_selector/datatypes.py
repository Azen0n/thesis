from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Type

TOPIC_THRESHOLD_LOW = 61
TOPIC_THRESHOLD_MEDIUM = 76
TOPIC_THRESHOLD_HIGH = 91
TOPIC_MAX_POINTS = 100
THEORY_TO_PRACTICE = 0.4

POINTS_EASY = 2
POINTS_NORMAL = 5
POINTS_HARD = 9

DIFFICULTY_THRESHOLD_NORMAL = 3
DIFFICULTY_THRESHOLD_HARD = 2

SUB_TOPIC_POINTS_COEF = 1 / 3


@dataclass
class Topic:
    title: str

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

    def __hash__(self):
        return hash(self.title)


@dataclass
class TopicProgress:
    _progress: float = 0
    max: float = TOPIC_MAX_POINTS

    @property
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, value: float):
        if value < 0:
            self._progress = 0
        elif value > self.max:
            self._progress = self.max
        else:
            self._progress = value

    def add(self, value: float):
        self.progress += value

    def is_low_reached(self) -> bool:
        low = self.max * (TOPIC_THRESHOLD_LOW / TOPIC_MAX_POINTS)
        return self._progress >= low

    def is_medium_reached(self) -> bool:
        medium = self.max * (TOPIC_THRESHOLD_MEDIUM / TOPIC_MAX_POINTS)
        return self._progress >= medium

    def is_high_reached(self) -> bool:
        high = self.max * (TOPIC_THRESHOLD_HIGH / TOPIC_MAX_POINTS)
        return self._progress >= high

    def is_completed(self) -> bool:
        return self._progress >= self.max


@dataclass
class TheoryProgress(TopicProgress):
    max: float = TOPIC_MAX_POINTS * THEORY_TO_PRACTICE


@dataclass
class PracticeProgress(TopicProgress):
    max: float = TOPIC_MAX_POINTS * (1 - THEORY_TO_PRACTICE)
    weakest_link_queue: list[PracticeProblem] = field(default_factory=list)
    is_time_to_throw_weakest_link: bool = False
    weakest_links: set[Topic] = None

    def remove_weakest_link_from_queue(self, topic: Topic):
        self.weakest_link_queue = [problem for problem in self.weakest_link_queue
                                   if topic not in problem.sub_topics]


@dataclass
class Progress:
    topic: Topic
    theory: TheoryProgress = field(default_factory=TheoryProgress)
    practice: PracticeProgress = field(default_factory=PracticeProgress)
    practice_difficulty: dict = None

    @property
    def progress(self) -> float:
        return self.theory.progress + self.practice.progress

    def __post_init__(self):
        self.practice_difficulty = {
            Difficulty.EASY: DIFFICULTY_THRESHOLD_NORMAL
            if self.theory.is_medium_reached() else 0,
            Difficulty.NORMAL: DIFFICULTY_THRESHOLD_HARD
            if self.theory.is_high_reached() else 0,
            Difficulty.HARD: 0
        }

    def max_difficulty(self):
        if self.theory.is_high_reached():
            return Difficulty.HARD
        if self.practice_difficulty[Difficulty.NORMAL] >= DIFFICULTY_THRESHOLD_HARD:
            return Difficulty.HARD
        if self.theory.is_medium_reached():
            return Difficulty.NORMAL
        if self.practice_difficulty[Difficulty.EASY] >= DIFFICULTY_THRESHOLD_NORMAL:
            return Difficulty.NORMAL
        if self.theory.is_low_reached():
            return Difficulty.EASY
        raise ValueError('Тест по теории не завершен.')


@dataclass
class Attempt:
    problem: Problem
    is_solved: bool


@dataclass
class AttemptTheory(Attempt):
    problem: TheoryProblem
    is_solved: bool


@dataclass
class AttemptPractice(Attempt):
    problem: PracticeProblem
    is_solved: bool


class Difficulty(Enum):
    EASY = 1
    NORMAL = 2
    HARD = 3

    def decrease(self) -> Difficulty:
        try:
            return Difficulty(self.value - 1)
        except ValueError:
            return self

    def increase(self) -> Difficulty:
        try:
            return Difficulty(self.value + 1)
        except ValueError:
            return self

    def to_points(self) -> float:
        return POINTS[self]


POINTS = {
    Difficulty.EASY: POINTS_EASY,
    Difficulty.NORMAL: POINTS_NORMAL,
    Difficulty.HARD: POINTS_HARD
}


@dataclass
class Problem:
    id: int
    difficulty: Difficulty
    main_topic: Topic
    sub_topics: set[Topic]
    is_theory: bool = None

    def is_available_for(self, user: User) -> bool:
        """Возвращает True если задание из текущей темы пользователя
        и по всем подтемам этого задания пройден теоретический тест.
        """
        if self.main_topic != user.current_topic.topic:
            return False
        x = user.topics_with_theory_completed()
        if all([topic in [progress.topic for progress
                          in user.topics_with_theory_completed()]
                for topic in self.sub_topics]):
            return True
        return False

    def is_easier_or_same(self, difficulty: Difficulty) -> bool:
        return self.difficulty.value <= difficulty.value

    def __str__(self) -> str:
        return (f'Problem(id={self.id},'
                f' difficulty={self.difficulty.name},'
                f' main_topic={self.main_topic},'
                f' sub_topics={self.sub_topics})')


@dataclass
class TheoryProblem(Problem):
    is_theory: bool = True

    def __str__(self) -> str:
        return (f'TheoryProblem(id={self.id},'
                f' difficulty={self.difficulty.name},'
                f' main_topic={self.main_topic},'
                f' sub_topics={self.sub_topics})')


@dataclass
class PracticeProblem(Problem):
    is_theory: bool = False

    def __str__(self) -> str:
        return (f'PracticeProblem(id={self.id},'
                f' difficulty={self.difficulty.name},'
                f' main_topic={self.main_topic},'
                f' sub_topics={self.sub_topics})')


@dataclass
class AttemptManager:
    user: User
    type: Type[Attempt]
    attempts: list[Attempt] = field(default_factory=list)

    def __post_init__(self):
        if not (self.type == AttemptTheory or self.type == AttemptPractice):
            raise TypeError('Неверный тип попытки.')

    def attempts_of_topic(self, topic: Topic) -> list[Attempt]:
        return [attempt for attempt in self.attempts
                if attempt.problem.main_topic == topic]

    def is_current_topic_in_progress(self) -> bool:
        attempts = self.attempts_of_topic(self.user.current_topic.topic)
        return len(attempts) > 0

    def was_attempt_on_problem(self, problem: Problem) -> bool:
        attempt = (attempt for attempt in self.attempts
                   if attempt.problem == problem)
        return True if next(attempt, False) else False

    def make_attempt(self, problem: Problem, is_solved: bool):
        """Эмуляция решения задания."""
        attempt = self.type(problem, is_solved)
        self.attempts.append(attempt)
        if not is_solved:
            return
        self.add_points(problem)

    def add_points(self, problem: Problem):
        progress = self.user.find_topic_progress(problem=problem)
        if problem.is_theory:
            progress.theory.add(problem.difficulty.to_points())
            self.add_points_to_sub_topics(problem)
        else:
            progress.practice.add(problem.difficulty.to_points())
            self.add_points_to_sub_topics(problem)
            progress.practice_difficulty[problem.difficulty] += 1

    def add_points_to_sub_topics(self, problem: Problem):
        for sub_topic in problem.sub_topics:
            progress = self.user.find_topic_progress(topic=sub_topic)
            points = problem.difficulty.to_points() * SUB_TOPIC_POINTS_COEF
            if problem.is_theory:
                progress.theory.add(points)
            else:
                progress.practice.add(points)


@dataclass
class User:
    id: int
    progress: list[Progress]
    current_topic: Progress = None
    theory: AttemptManager = None
    practice: AttemptManager = None
    difficulty_preference: Difficulty = Difficulty.EASY

    def __post_init__(self):
        self.current_topic = self.progress[0]
        self.theory = AttemptManager(self, AttemptTheory)
        self.practice = AttemptManager(self, AttemptPractice)

    def topics_with_theory_completed(self) -> list[Progress]:
        return [progress for progress in self.progress
                if progress.theory.is_low_reached()]

    def find_topic_progress(self, problem: Problem = None, topic: Topic = None) -> Progress:
        """Возвращает Progress по теме задания."""
        if problem is not None:
            f = filter(lambda x: x.topic == problem.main_topic, self.progress)
        elif topic is not None:
            f = filter(lambda x: x.topic == topic, self.progress)
        else:
            raise ValueError('Не задан параметр фильтра.')
        progress = next(f, None)
        if progress is None:
            raise NotImplementedError('Прогресс темы не найден.')
        return progress

    def __str__(self):
        return (f'id: {self.id}, topics:'
                f' {", ".join([progress.topic.title for progress in self.progress])}\n')
