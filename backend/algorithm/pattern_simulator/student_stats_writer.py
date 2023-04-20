from django.contrib.auth.models import User
from django.db.models import QuerySet
from prettytable import PrettyTable

from algorithm.models import Progress, UserAnswer
from courses.models import Semester, Type, Difficulty


def write_student_stats_to_file(filepath: str, user: User, semester: Semester):
    """Записывает баллы студента по каждой теме,
    ответы на задания и общую статистику по решениям в текстовый файл.
    """
    write_progresses(filepath, user, semester)
    write_user_answers(filepath, user, semester)


def write_progresses(filepath: str, user: User, semester: Semester):
    """Записывает баллы студента по каждой теме в текстовый файл."""
    progresses = Progress.objects.filter(user=user, semester=semester)
    with open(filepath, 'w') as f:
        f.write(f'user: {user}   semester: {semester}\n')
        for progress in progresses.order_by('topic__created_at'):
            f.write(f'{progress.topic} -'
                    f' {progress.theory_points:.2f}'
                    f' / {progress.practice_points:.2f}'
                    f' / {progress.theory_points + progress.practice_points:.2f}'
                    f'\n')


def write_user_answers(filepath: str, user: User, semester: Semester):
    """Записывает ответы пользователя на задания в текстовый файл."""
    user_answers = UserAnswer.objects.filter(user=user, semester=semester)
    write_user_answers_stats(filepath, user_answers)
    with open(filepath, 'a') as f:
        table = PrettyTable()
        table.field_names = ['#', 'название', 'сложность', 'время на решение', 'основная тема', 'подтемы', 'решено']
        for i, answer in enumerate(user_answers.order_by('created_at'), start=1):
            table.add_row([
                i,
                answer.problem.title,
                answer.problem.get_difficulty_display(),
                answer.problem.time_to_solve_in_seconds,
                answer.problem.main_topic.title,
                ", ".join([topic.title for topic in answer.problem.sub_topics.all().order_by('created_at')]),
                'да' if answer.is_solved else 'нет'])
        f.write(f'\n{table}')


def write_user_answers_stats(filepath: str, user_answers: QuerySet[UserAnswer]):
    """Записывает количество решенных и нерешенных заданий
    и их сложность в текстовый файл.
    """
    with open(filepath, 'a') as f:
        f.write(f'\nВсего заданий: {user_answers.count()}'
                f'\nТеория {user_answer_stats(user_answers, types=[Type.MULTIPLE_CHOICE_RADIO])}'
                f'\nПрактика {user_answer_stats(user_answers, types=[Type.FILL_IN_SINGLE_BLANK])}')


def user_answer_stats(user_answers: QuerySet[UserAnswer], types: list[Type]) -> str:
    """Возвращает статистику решенных и нерешенных заданий по типам."""
    answers = user_answers.filter(problem__type__in=types)
    correct_answers = answers.filter(is_solved=True)
    incorrect_answers = answers.filter(is_solved=False)
    return (f'всего: {answers.count()}'
            f'\nРешено: {answers_stats_by_difficulty(correct_answers, answers)}'
            f'\nНе решено: {answers_stats_by_difficulty(incorrect_answers, answers)}\n')


def answers_stats_by_difficulty(solved_answers: QuerySet[UserAnswer], all_answers: QuerySet[UserAnswer]) -> str:
    """Возвращает строку с количеством решенных/нерешенных заданий по сложности."""
    return (f'{solved_answers.count()} '
            f'({0 if not all_answers.count() else solved_answers.count() / all_answers.count() * 100:.2f}%)\n'
            f' - легких: {solved_answers.filter(problem__difficulty=Difficulty.EASY).count()}\n'
            f' - нормальных: {solved_answers.filter(problem__difficulty=Difficulty.NORMAL).count()}\n'
            f' - сложных: {solved_answers.filter(problem__difficulty=Difficulty.HARD).count()}\n')
