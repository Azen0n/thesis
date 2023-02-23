import datetime
import random

from django.contrib.auth.models import User

from algorithm.models import TopicGraphEdge
from algorithm.utils import create_user_progress
from courses.models import (Course, Semester, Module, Topic, Problem,
                            THEORY_TYPES, Difficulty, Type, PRACTICE_TYPES)

random.seed(42)


def generate_test_data():
    semester = Semester.objects.filter(course__title='Test Course').first()
    if not semester:
        semester = create_test_semester()
        create_test_topics(semester.course, number_of_topics=10)
        create_problems(semester.course)
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
    for i in range(number_of_topics):
        topic = Topic.objects.create(
            title=f'Topic {i + 1}',
            time_to_complete=5,
            is_required=False,
            module=module
        )
        module.topic_set.add(topic)


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
    problem = Problem.objects.create(
        title=problem_title,
        description='Lorem Ipsum',
        type=random.choice(types),
        difficulty=random.choice([Difficulty.EASY,
                                  Difficulty.NORMAL,
                                  Difficulty.HARD]),
        main_topic=topic
    )
    if available_sub_topics:
        sub_topics = random.choices(available_sub_topics,
                                    k=random.randint(0, 2))
        if sub_topics:
            problem.sub_topics.add(*sub_topics)


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
