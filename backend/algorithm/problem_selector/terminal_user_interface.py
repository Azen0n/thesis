from django.contrib.auth.models import User
from django.db.models import QuerySet

from algorithm.models import Progress
from algorithm.utils import initialize_algorithm
from answers.create_answer import create_user_answer
from courses.models import Semester, Problem

problem_selector = initialize_algorithm()


def main():
    user = User.objects.get(username='test_user')
    semester = Semester.objects.filter(course__title='Test Course').first()
    progresses = print_progress(user, semester)
    progress = select_progress(progresses)
    while True:
        try:
            progress = perform_action(user, semester, progress)
        except NotImplementedError as e:
            print(e)
            progress = select_progress(progresses)


def print_progress(user: User, semester: Semester) -> QuerySet[Progress]:
    """Выводит список тем курса и переход к практике
    и возвращает QuerySet с прогрессами.
    """
    print('Выберите тему, чтобы получить следующее теоретическое задание')
    progresses = Progress.objects.filter(user=user, semester=semester).order_by()
    for i, progress in enumerate(progresses, start=1):
        print(f'( {i} ) {progress}')
    print('------------------------------')
    print(f'( {len(progresses) + 1} ) Перейти к практическим заданиям')
    return progresses


def select_progress(progresses: QuerySet[Progress]) -> Progress | None:
    """Возвращает выбранный пользователем прогресс или None,
    если выбран переход к практике.
    """
    topic_number = int(input('Выберите тему: '))
    while topic_number - 1 < 0 or topic_number - 1 > len(progresses):
        topic_number = int(input('Выберите тему: '))
    if topic_number - 1 == len(progresses):
        return None
    return progresses[topic_number - 1]


def perform_action(user: User, semester: Semester, progress: Progress | None) -> Progress:
    """Подбирает следующее задание или возвращает пользователя к выбору темы."""
    if progress is None:
        practice_problem(user, semester)
        action = select_action()
        while action == '1':
            practice_problem(user, semester)
            action = select_action()
    else:
        theory_problem(progress)
        action = select_action()
        while action == '1':
            theory_problem(progress)
            progress.refresh_from_db()
            action = select_action()
    if action == '2':
        progresses = print_progress(user, semester)
        progress = select_progress(progresses)
    return progress


def theory_problem(progress: Progress):
    """Подбирает следующее задание по практике."""
    problem = problem_selector.next_theory_problem(progress)
    print_problem_and_create_answer(progress.user, progress.semester, problem)


def practice_problem(user: User, semester: Semester):
    """Подбирает следующее задание по практике."""
    problem = problem_selector.next_practice_problem(user, semester)
    print_problem_and_create_answer(user, semester, problem)


def select_action() -> str:
    """Возвращает ввод команды пользователя по переходу
    к заданию или списку тем.
    """
    actions = ('[ 1 ] следующее задание'
               '  [ 2 ] выбрать тему\n')
    action = input(actions)
    while action not in ['1', '2']:
        action = input(actions)
    return action


def print_problem_and_create_answer(user: User, semester: Semester, problem: Problem):
    """Выводит информацию о задании и записывает ответ пользователя
    на него в базу данных.
    """
    print_problem(problem)
    create_answer_on_problem(user, semester, problem)
    progress = Progress.objects.filter(
        user=user,
        semester=semester,
        topic=problem.main_topic
    ).first()
    print(f'{progress}\n')


def print_problem(problem: Problem):
    """Выводит информацию о задании и темах в консоль."""
    print(f'{problem.main_topic}. {problem.title} (сложность: {problem.difficulty})'
          f'\n{problem.description}')
    if problem.sub_topics.exists():
        print('Подтемы: ', end='')
        print(', '.join([f'{topic}' for topic in problem.sub_topics.all()]))


def create_answer_on_problem(user: User, semester: Semester, problem: Problem):
    """Записывает ответ пользователя на задание в базу данных."""
    answer = int(input('[ 1 ] Правильный ответ  [2] Неправильный ответ\n'))
    if answer not in [1, 2]:
        answer = int(input('[ 1 ] Правильный ответ  [2] Неправильный ответ\n'))
    answer = True if answer == 1 else False
    create_user_answer(user, semester, problem, answer)


if __name__ == '__main__':
    main()
