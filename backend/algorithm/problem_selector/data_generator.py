import datetime
import random

from django.contrib.auth.models import User

from algorithm.models import TopicGraphEdge
from algorithm.utils import create_user_progress
from answers.models import MultipleChoiceRadio, MultipleChoiceCheckbox, FillInSingleBlank
from config.settings import Constants
from courses.models import (Course, Semester, Module, Topic, Problem,
                            THEORY_TYPES, Difficulty, Type, PRACTICE_TYPES)

random.seed(42)


def generate_test_data():
    semester = Semester.objects.filter(course__title='Test Course').first()
    if not semester:
        semester = create_test_semester()
        create_test_topics(semester.course, number_of_topics=10)
        create_problems(semester.course)
        create_random_answers(semester.course)
        create_random_topic_graph(Topic.objects.filter(module__course=semester.course))
    user = User.objects.filter(username='test_user').first()
    if not user:
        user = create_test_user()
        semester.students.add(user)
        create_user_progress(semester, user)


def create_test_semester() -> Semester:
    """Создает курс "Test Course", и возвращает семестр по нему."""
    course = Course.objects.create(
        title='Test Course',
        description='Lorem Ipsum',
        duration=50
    )
    semester = Semester.objects.create(
        course=course,
        started_at=datetime.datetime.utcnow(),
        ended_at=datetime.datetime.utcnow()
    )
    return semester


def create_test_user() -> User:
    """Создает и возвращает пользователя test_user."""
    return User.objects.create_user(username='test_user',
                                    email='example@mail.com',
                                    password='password')


def create_test_topics(course: Course, number_of_topics: int = 10):
    """Создает темы для курса."""
    module = Module.objects.create(
        title='Test Module',
        description='Lorem Ipsum',
        is_required=True,
        course=course
    )
    parent_topic = None
    for i in range(number_of_topics):
        topic = Topic.objects.create(
            title=f'Topic {i + 1}',
            time_to_complete=5,
            is_required=False,
            module=module,
            parent_topic=parent_topic
        )
        module.topic_set.add(topic)
        parent_topic = topic


def create_problems(course: Course,
                    number_of_theory_problems: int = 50,
                    number_of_practice_problems: int = 50):
    """Создает случайные теоретические и практические задания в каждой теме курса."""
    theory_problem_counter = 1
    practice_problem_counter = 1
    available_sub_topics = []
    for topic in course.module_set.filter(title='Test Module').first().topic_set.all():
        for i in range(number_of_theory_problems):
            create_problem(f'Theory Problem {theory_problem_counter}', topic,
                           available_sub_topics, THEORY_TYPES)
            theory_problem_counter += 1
        for i in range(number_of_practice_problems):
            create_problem(f'Practice Problem {practice_problem_counter}', topic,
                           available_sub_topics, PRACTICE_TYPES)
            practice_problem_counter += 1
        available_sub_topics.append(topic)


def create_problem(problem_title: str, topic: Topic,
                   available_sub_topics: list[Topic],
                   types: list[Type]):
    """Создает задание со случайными подтемами."""
    number_of_sub_topics = generate_number_of_sub_topics(len(available_sub_topics))
    difficulty = random.choice([Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD])
    time_to_solve_in_seconds = generate_time_to_solve_in_seconds(types, difficulty,
                                                                 number_of_sub_topics)
    problem = Problem.objects.create(
        title=problem_title,
        description='Lorem Ipsum',
        type=random.choice(types),
        difficulty=difficulty,
        time_to_solve_in_seconds=time_to_solve_in_seconds,
        main_topic=topic
    )
    if available_sub_topics:
        sub_topics = random.sample(available_sub_topics, k=number_of_sub_topics)
        if sub_topics:
            problem.sub_topics.add(*sub_topics)


def generate_time_to_solve_in_seconds(types: list[Type], difficulty: Difficulty,
                                      number_of_sub_topics: int) -> float:
    """Возвращает количество секунд на решение задания."""
    if types == THEORY_TYPES:
        time_to_solve_in_seconds = random.randint(1, 5) + (
                100 * difficulty.value - 100) + 10 * (1 + number_of_sub_topics)
    elif types == PRACTICE_TYPES:
        time_to_solve_in_seconds = random.randint(1, 5) * 5 + (
                500 * difficulty.value - 200) + 10 * (1 + number_of_sub_topics)
    else:
        raise ValueError(f'Неизвестные типы заданий: {", ".join(types)}.')
    return time_to_solve_in_seconds


def generate_number_of_sub_topics(number_of_available_sub_topics: int) -> int:
    """Возвращает случайное количество подтем."""
    if number_of_available_sub_topics > Constants.MAX_NUMBER_OF_SUB_TOPICS:
        max_number_of_sub_topics = Constants.MAX_NUMBER_OF_SUB_TOPICS
    else:
        max_number_of_sub_topics = number_of_available_sub_topics
    return random.randint(0, max_number_of_sub_topics)


def create_random_topic_graph(topics: list[Topic]):
    """Создает граф тем со случайными весами."""
    course = topics[0].module.course
    for topic1 in topics:
        for topic2 in topics:
            if topic1 == topic2:
                continue
            TopicGraphEdge.objects.create(
                course=course,
                topic1=topic1,
                topic2=topic2,
                weight=random.random()
            )


def create_random_answers(course: Course):
    """Создает случайные ответы на задания."""
    problems = Problem.objects.filter(main_topic__module__course=course)
    for problem in problems:
        match problem.type:
            case Type.MULTIPLE_CHOICE_RADIO.value:
                create_random_multiple_choice_radio_answers(problem)
            case Type.MULTIPLE_CHOICE_CHECKBOX.value:
                create_random_multiple_choice_checkbox_answers(problem)
            case Type.FILL_IN_SINGLE_BLANK.value:
                create_random_fill_in_single_blank_answers(problem)
            case Type.CODE.value:
                pass
            case other_type:
                raise ValueError(f'Неизвестный тип {other_type}')


def create_random_multiple_choice_radio_answers(problem: Problem):
    """Создает случайные варианты ответа с одним правильным."""
    correct = random.randint(1, 4)
    for i in range(1, 5):
        if i == correct:
            MultipleChoiceRadio.objects.create(text='True', is_correct=True, problem=problem)
        else:
            MultipleChoiceRadio.objects.create(text='False', is_correct=False, problem=problem)


def create_random_multiple_choice_checkbox_answers(problem: Problem):
    """Создает случайные варианты ответа с несколькими правильными (от двух до четырех)."""
    correct = random.sample([1, 2, 3, 4], random.randint(2, 4))
    for i in range(1, 5):
        if i in correct:
            MultipleChoiceCheckbox.objects.create(text='True', is_correct=True, problem=problem)
        else:
            MultipleChoiceCheckbox.objects.create(text='False', is_correct=False, problem=problem)


def create_random_fill_in_single_blank_answers(problem: Problem):
    """Создает верный ответ на задание с типом заполнения пропуска."""
    FillInSingleBlank.objects.create(text='True', problem=problem)
