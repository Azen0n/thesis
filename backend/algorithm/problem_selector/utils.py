import random
from typing import Type

from datatypes import (Topic, Problem, Difficulty, User, Progress,
                       TheoryProblem, PracticeProblem)


def get_sample_data(number_of_users: int = 1,
                    number_of_topics: int = 3,
                    number_of_theory_problems: int = 300,
                    number_of_practice_problems: int = 300):
    """Возвращает случайные данные для алгоритма."""
    topics = [Topic(f'Тема {i + 1}') for i in range(number_of_topics)]
    users = generate_users(number_of_users, topics)
    theory_problems = generate_problems(TheoryProblem,
                                        number_of_theory_problems,
                                        topics)
    practice_problems = generate_problems(PracticeProblem,
                                          number_of_practice_problems,
                                          topics)
    return users, topics, theory_problems, practice_problems


def generate_problems(problem_type: Type[Problem],
                      number_of_problems: int, topics: list[Topic]) -> list:
    """Генерирует случайные задания заданного типа."""
    problems = []
    for i in range(number_of_problems):
        main_topic = random.choice(topics)
        sub_topics = generate_sub_topics(main_topic, topics)
        problem = problem_type(i + 1, random.choice(list(Difficulty)),
                               main_topic, sub_topics)
        problems.append(problem)
    return problems


def generate_sub_topics(main_topic: Topic, topics: list[Topic],
                        min_sub_topics: int = 0,
                        max_sub_topics: int = 2) -> set[Topic]:
    """Генерирует случайные подтемы к заданной основной теме.
    Подтемами могут быть темы, идущее до основной.
    """
    index = topics.index(main_topic)
    match index:
        case 0:
            sub_topics = []
        case 1:
            min_sub_topics = 1 if min_sub_topics == 1 else 0
            max_sub_topics = 1 if min_sub_topics >= 1 else 0
            number_of_sub_topics = random.randint(min_sub_topics,
                                                  max_sub_topics)
            sub_topics = [topics[0]] if number_of_sub_topics else []
        case _:
            number_of_sub_topics = random.randint(min_sub_topics,
                                                  max_sub_topics)
            sub_topics = random.choices(topics[:index],
                                        k=number_of_sub_topics)
    if main_topic in sub_topics:
        sub_topics.remove(main_topic)
    return set(sub_topics)


def generate_users(number_of_users: int, topics: list[Topic]) -> list[User]:
    """Возвращает список пользователей."""
    users = []
    for i in range(number_of_users):
        progress = [Progress(topic) for topic in topics]
        user = User(id=i + 1, progress=progress)
        users.append(user)
    return users
