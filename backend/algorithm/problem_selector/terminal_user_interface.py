from django.contrib.auth.models import User

from algorithm.models import Progress, UserCurrentProgress
from algorithm.utils import initialize_algorithm
from answers.create_answer import create_user_answer
from courses.models import Semester, Problem

problem_selector = initialize_algorithm()


def main():
    user = User.objects.get(username='test_user')
    semester = Semester.objects.filter(course__title='Test Course').first()
    current_progress = change_current_progress(user, semester)
    while True:
        try:
            current_progress = perform_action(select_action(), current_progress)
        except NotImplementedError as e:
            print(e)


def change_current_progress(user: User, semester: Semester) -> UserCurrentProgress:
    progress = print_and_select_progress(user, semester)
    current_progress = UserCurrentProgress.objects.get(user=user, semester=semester)
    current_progress.progress = progress
    current_progress.save()
    return current_progress


def print_and_select_progress(user: User, semester: Semester) -> Progress:
    progresses = Progress.objects.filter(user=user, semester=semester)
    for i, progress in enumerate(progresses, start=1):
        print(f'( {i} ) {progress}')
    topic_number = int(input('Выберите тему: '))
    while topic_number - 1 < 0 or topic_number - 1 >= len(progresses):
        topic_number = int(input('Выберите тему: '))
    return progresses[topic_number - 1]


def select_action() -> int:
    actions = ('[ 1 ] следующее задание по теории'
               '  [ 2 ] следующее задание по практике'
               '  [ 3 ] выбрать другую тему\n')
    action = int(input(actions))
    while action not in [1, 2, 3]:
        action = int(input(actions))
    return action


def perform_action(action: int, current_progress: UserCurrentProgress) -> UserCurrentProgress:
    match action:
        case 1:
            problem = problem_selector.next_theory_problem(current_progress)
            create_answer_on_problem(problem, current_progress)
            current_progress.refresh_from_db()
            print(current_progress.progress)
        case 2:
            problem = problem_selector.next_practice_problem(current_progress)
            create_answer_on_problem(problem, current_progress)
            current_progress.refresh_from_db()
            print(current_progress.progress)
        case 3:
            current_progress = change_current_progress(current_progress.user,
                                                       current_progress.semester)
        case _:
            raise ValueError('action not in [1, 2, 3]')
    return current_progress


def create_answer_on_problem(problem: Problem, current_progress: UserCurrentProgress):
    print(f'{problem.title} (сложность: {problem.difficulty})\n{problem.description}')
    if problem.sub_topics.exists():
        print('Подтемы: ', end='')
        print(', '.join([f'{topic}' for topic in problem.sub_topics.all()]))
    answer = int(input('[ 1 ] Правильный ответ  [2] Неправильный ответ\n'))
    if answer not in [1, 2]:
        answer = int(input('[ 1 ] Правильный ответ  [2] Неправильный ответ\n'))
    answer = True if answer == 1 else False
    create_user_answer(current_progress, problem, answer)


if __name__ == '__main__':
    main()
