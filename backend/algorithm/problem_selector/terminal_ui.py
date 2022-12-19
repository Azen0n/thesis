from __future__ import annotations
import random

from problem_selector import ProblemSelector
from datatypes import User
from utils import get_sample_data

random.seed(42)


def main():
    users, topics, theory_problems, practice_problems = get_sample_data(
        number_of_users=1,
        number_of_topics=6,
        number_of_theory_problems=300,
        number_of_practice_problems=300
    )

    algorithm = ProblemSelector(users, topics,
                                theory_problems=theory_problems,
                                practice_problems=practice_problems)
    print(algorithm)
    current_user = users[0]
    run(algorithm, current_user)


def run(algorithm: ProblemSelector, current_user: User):
    for i in range(4):
        current_user.progress[i].theory.progress = 24.4

    select_topic(algorithm, current_user)
    while True:
        try:
            print_current_topic_progress(current_user)
            print_commands(current_user)
            parse_command(input(), algorithm, current_user)

        except Exception as e:
            print(f'ОШИБКА: {e}')


def print_topics(algorithm: ProblemSelector, current_user: User):
    """Выводит в консоль список тем и прогресс текущего
    пользователя по ним.
    """
    for i, topic in enumerate(algorithm.topics):
        print(f'[{i + 1}] {topic}\t\t\t{current_user.progress[i].theory.progress} /'
              f' {current_user.progress[i].practice.progress} /'
              f' {current_user.progress[i].progress}')


def print_commands(current_user: User):
    is_theory = current_user.current_topic.theory.is_low_reached()
    commands = (f'[1] теория  [2] практика'
                f'{" (!)" if is_theory else ""}  [back] : ')
    print(commands, end='')


def parse_command(command: str, algorithm: ProblemSelector, current_user: User):
    match command:
        case '1':
            next_theory_problem(algorithm, current_user)
        case '2':
            next_practice_problem(algorithm, current_user)
        case 'back':
            select_topic(algorithm, current_user)
        case _:
            command = input('Неизвестная команда. Выберите действие: ')
            parse_command(command, algorithm, current_user)


def print_current_topic_progress(current_user: User):
    print(f'Прогресс темы "{current_user.current_topic.topic.title}":'
          f' теория: {current_user.current_topic.theory.progress} /'
          f' практика: {current_user.current_topic.practice.progress} /'
          f' общий: {current_user.current_topic.progress}')


def select_topic(algorithm: ProblemSelector, current_user: User):
    print_topics(algorithm, current_user)
    topic_index = int(input('Выберите тему: ')) - 1
    current_user.current_topic = current_user.progress[topic_index]


def next_theory_problem(algorithm: ProblemSelector, current_user: User):
    problem = algorithm.next_theory_problem(current_user)
    print(problem)
    answer = input('Ответ на задание (True/False): ') == 'True'
    current_user.theory.make_attempt(problem, is_solved=answer)


def next_practice_problem(algorithm: ProblemSelector, current_user: User):
    problem = algorithm.next_practice_problem(current_user)
    print(problem)
    answer = input('Ответ на задание (True/False): ') == 'True'
    current_user.practice.make_attempt(problem, is_solved=answer)


if __name__ == '__main__':
    main()
