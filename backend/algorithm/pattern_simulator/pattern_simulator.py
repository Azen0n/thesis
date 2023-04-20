import json
import random
from dataclasses import dataclass

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import F
from django.test import RequestFactory
from django.urls import reverse

from algorithm.models import Progress
from algorithm.pattern_simulator.patterns import Pattern, Style
from algorithm.pattern_simulator.student_stats_writer import write_student_stats_to_file
from algorithm.problem_selector import next_theory_problem, next_practice_problem
from algorithm.views import enroll_semester
from answers.models import MultipleChoiceRadio, FillInSingleBlank
from answers.views import validate_answer
from config.settings import Constants
from courses.models import Semester, SemesterCode, Problem, Type, Topic

random.seed(42)


@dataclass
class PatternSimulator:
    pattern: Pattern
    user: User | None = None
    semester: Semester | None = None

    def __init__(self, pattern: Pattern, username: str = None, semester_title: str = None):
        self.pattern = pattern
        self.set_up(username, semester_title)

    def set_up(self, username: str = None, semester_title: str = None):
        """Создает пользователя для проведения симуляции. Если username не указан,
        создается пользователь с username "test_user".
        Пользователь записывается на курс с названием semester_title.
        Если название не указано, пользователь записывается на курс "Test Course".
        """
        self.user = self.create_user(username)
        semester_title = 'Test Course' if semester_title is None else semester_title
        self.semester = Semester.objects.get(course__title=semester_title)
        url = reverse('enroll', args=[self.semester.pk])
        request = RequestFactory().get(url, content_type='application/json')
        request._body = json.dumps({'code': SemesterCode.objects.get(semester=self.semester).code})
        request.user = self.user
        enroll_semester(request, self.semester.pk)

    def create_user(self, username: str = None) -> User | None:
        """Возвращает нового пользователя с username. Если username не указан,
        создается пользователь с username "test_user".
        """
        username = 'test_user' if username is None else username
        try:
            user = User.objects.create_user(username=username, password='password')
        except IntegrityError:
            self.tear_down(username)
            user = User.objects.create_user(username=username, password='password')
        return user

    def tear_down(self, username: str = None):
        """Удаляет все данные о пользователе с username. Если username не указан,
        удаляются данные о пользователе с username "test_user"."""
        username = 'test_user' if username is None else username
        User.objects.filter(username=username).delete()
        self.user = None

    def run(self):
        match self.pattern.style:
            case Style.TOPIC_BASED:
                self.topic_based_simulation()
            case Style.THEORY_FIRST:
                self.theory_first_simulation()
            case _:
                raise ValueError('Неизвестный стиль.')
        self.export_simulation_results()
        self.tear_down()

    def topic_based_simulation(self):
        """Прохождение теории и практики чередуется: сначала закрывается теория
        по теме, затем практика по ней.
        """
        raise NotImplementedError()

    def theory_first_simulation(self):
        """Сначала проходится теория по всем темам, затем практика."""
        topics = self.semester.course.module_set.first().topic_set.all().order_by('created_at')
        for topic in topics:
            self.complete_topic_theory_to_low_points(topic)
        for topic in topics:
            self.complete_topic_theory_to_target_points(topic)
        self.complete_practice_in_all_topics()

    def complete_topic_theory_to_low_points(self, topic: Topic):
        """Завершает теорию по теме на минимальный балл."""
        progress = Progress.objects.get(user=self.user, semester=self.semester, topic=topic)
        while not progress.is_theory_low_reached():
            problem = next_theory_problem(progress)
            self.solve_problem(problem, is_solved=self.pattern.is_next_problem_solved())
            progress.refresh_from_db()

    def complete_topic_theory_to_target_points(self, topic: Topic):
        """Завершает теорию по теме на требуемый балл."""
        progress = Progress.objects.get(user=self.user, semester=self.semester, topic=topic)
        target_points = Constants.TOPIC_THEORY_MAX_POINTS * self.pattern.target_points_coefficient
        while progress.theory_points < target_points:
            problem = next_theory_problem(progress)
            self.solve_problem(problem, is_solved=self.pattern.is_next_problem_solved())
            progress.refresh_from_db()

    def solve_problem(self, problem: Problem, is_solved: bool):
        """Отправляет ответ пользователя на задание."""
        match problem.type:
            case Type.MULTIPLE_CHOICE_RADIO:
                option = solve_multiple_choice_radio(problem, is_solved)
                body = {'answer_id': str(option.id), 'type': problem.type}
            case Type.FILL_IN_SINGLE_BLANK:
                value = solve_fill_in_single_blank(problem, is_solved)
                body = {'value': value, 'problem_id': str(problem.id), 'type': problem.type}
            case _:
                raise NotImplementedError(f'Проверка типа задания "{problem.type}" недоступна.')
        request = self.create_validate_problem_request(problem, body)
        validate_answer(request, self.semester.pk, problem.pk)

    def create_validate_problem_request(self, problem: Problem, body: dict):
        url = reverse('validate_answer', args=[self.semester.pk, problem.pk])
        request = RequestFactory().get(url, content_type='application/json')
        request._body = json.dumps(body)
        request.user = self.user
        return request

    def is_all_topics_completed(self) -> bool:
        """Возвращает True, если по всем темах набран необходимый балл."""
        practice_points = self.get_all_topic_points()
        max_points = Constants.TOPIC_THEORY_MAX_POINTS + Constants.TOPIC_PRACTICE_MAX_POINTS
        target_points = max_points * self.pattern.target_points_coefficient
        return not any([points < target_points for points in practice_points])

    def get_all_topic_points(self) -> list[float]:
        """Возвращает список баллов по практике."""
        progresses = Progress.objects.filter(user=self.user, semester=self.semester)
        total_points = progresses.annotate(
            total_points=F('theory_points') + F('practice_points')
        ).values_list('total_points', flat=True)
        return total_points

    def complete_practice_in_all_topics(self):
        """Завершает практику по всем темам."""
        while not self.is_all_topics_completed():
            problem = next_practice_problem(self.user, self.semester)
            self.solve_problem(problem, is_solved=self.pattern.is_next_problem_solved())

    def export_simulation_results(self):
        """Записывает результат симуляции в тестовый файл."""
        filepath = f'output{random.randint(int(1e5), int(1e6))}.txt'
        write_student_stats_to_file(filepath, self.user, self.semester)


def solve_multiple_choice_radio(problem: Problem, is_solved: bool) -> MultipleChoiceRadio:
    """Возвращает правильный или неправильный вариант ответа на задание
    с типом "выбор одного варианта ответа".
    """
    options = MultipleChoiceRadio.objects.filter(problem=problem)
    if is_solved:
        return options.filter(is_correct=True).first()
    return random.choice(options.filter(is_correct=False))


def solve_fill_in_single_blank(problem: Problem, is_solved: bool) -> str:
    """Возвращает правильный или неправильный вариант ответа на задание
    с типом "заполнение пропуска".
    """
    options = FillInSingleBlank.objects.filter(problem=problem)
    if is_solved:
        return random.choice(options).text
    return str(random.uniform(-1, 1))
