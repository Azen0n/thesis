import random

from django.contrib.auth.models import User
from django.utils import timezone

from algorithm.models import (TopicGraphEdge, Progress, UserWeakestLinkState,
                              WeakestLinkState, UserAnswer, WeakestLinkProblem,
                              WeakestLinkTopic)
from algorithm.utils import create_user_progress_if_not_exists
from answers.models import (MultipleChoiceRadio, MultipleChoiceCheckbox,
                            FillInSingleBlank)
from config.settings import Constants
from courses.models import (Course, Semester, Module, Topic, Problem,
                            THEORY_TYPES, Difficulty, Type, PRACTICE_TYPES, SemesterCode)
from courses.utils import generate_join_code

random.seed(42)


def generate_test_data():
    """Создает тестовый курс с заданиями и семестру по нему.
    Создает и записывает на курс пользователя admin с правами администратора.
    """
    semester = Semester.objects.filter(course__title='Test Course').first()
    if not semester:
        semester = create_test_semester()
        teacher = create_teacher(semester)
        create_join_code(semester, teacher)
        create_test_modules_and_topics(semester.course,
                                       number_of_topics_in_modules=[1, 4, 3, 3, 4, 4])
        create_problems(semester.course)
        create_random_answers(semester.course)
        create_random_topic_graph(Topic.objects.filter(module__course=semester.course))
    user = User.objects.filter(username='admin').first()
    if not user:
        user = create_superuser()
    if user not in semester.students.all():
        semester.students.add(user)
    create_user_progress_if_not_exists(semester, user)


def create_test_semester() -> Semester:
    """Создает курс "Test Course", и возвращает семестр по нему."""
    course = Course.objects.create(
        title='Test Course',
        description='Lorem Ipsum',
        duration=50
    )
    semester = Semester.objects.create(
        course=course,
        started_at=timezone.now(),
        ended_at=timezone.now() + timezone.timedelta(days=30)
    )
    return semester


def create_join_code(semester: Semester, teacher: User):
    """Создает код для присоединения к курсу."""
    code = generate_join_code()
    SemesterCode.objects.create(semester=semester, teacher=teacher,
                                code=code, expired_at=semester.ended_at)


def create_superuser() -> User:
    """Создает и возвращает пользователя admin с правами администратора."""
    return User.objects.create_superuser(username='admin',
                                         email='admin@mail.com',
                                         password='admin')


def create_teacher(semester: Semester) -> User:
    """Создает и возвращает пользователя teacher, назначая его преподавателем курса."""
    teacher, _ = User.objects.get_or_create(username='teacher',
                                         email='teacher@mail.com',
                                         password='teacher')
    if teacher not in semester.teachers.all():
        semester.teachers.add(teacher)
    return teacher


def create_test_modules_and_topics(course: Course, number_of_topics_in_modules: list[int]):
    """Создает модули и темы для курса."""
    topic_index = 1
    parent_topic = None
    for i, number_of_topics in enumerate(number_of_topics_in_modules):
        module = Module.objects.create(
            title=f'Module {i + 1}',
            description='Lorem Ipsum',
            is_required=True,
            course=course
        )
        for _ in range(number_of_topics):
            topic = Topic.objects.create(
                title=f'Topic {topic_index}',
                time_to_complete=5,
                is_required=False,
                module=module,
                parent_topic=parent_topic
            )
            module.topic_set.add(topic)
            parent_topic = topic
            topic_index += 1


def create_problems(course: Course,
                    number_of_theory_problems: int = 50,
                    number_of_practice_problems: int = 50):
    """Создает случайные теоретические и практические задания в каждой теме курса."""
    theory_problem_counter = 1
    practice_problem_counter = 1
    available_sub_topics = []
    for module in course.module_set.all().order_by('created_at'):
        for topic in module.topic_set.all().order_by('created_at'):
            for i in range(number_of_theory_problems):
                create_problem(f'Theory Problem {theory_problem_counter}', topic,
                               available_sub_topics, [Type.MULTIPLE_CHOICE_RADIO])
                theory_problem_counter += 1
            for i in range(number_of_practice_problems):
                create_problem(f'Practice Problem {practice_problem_counter}', topic,
                               available_sub_topics, [Type.FILL_IN_SINGLE_BLANK])
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
    if set(types).issubset(set(THEORY_TYPES)):
        time_to_solve_in_seconds = random.randint(10, 50) + (
                60 * difficulty.value - 60) + 8 * (1 + number_of_sub_topics)
    elif set(types).issubset(set(PRACTICE_TYPES)):
        time_to_solve_in_seconds = random.randint(
            3 * difficulty.value,
            5 * difficulty.value
        ) * 20 + (180 * difficulty.value - 80) + 30 * (1 + number_of_sub_topics)
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


def clear_progresses_for_all_users_and_semesters():
    """Сбрасывает прогресс всех пользователей по всем курсам."""
    progresses = Progress.objects.all()
    for progress in progresses:
        progress.theory_points = 0.0
        progress.practice_points = 0.0
        progress.skill_level = Constants.AVERAGE_SKILL_LEVEL
        progress.save()


def clear_user_weakest_link_states():
    """Сбрасывает статус алгоритма поиска слабого звена."""
    user_weakest_link_states = UserWeakestLinkState.objects.all()
    for state in user_weakest_link_states:
        state.state = WeakestLinkState.NONE
        state.save()


def delete_and_clear_all_objects():
    """Удаляет и сбрасывает созданные пользователями объекты в процессе
    прохождения курсов.
    """
    UserAnswer.objects.all().delete()
    clear_progresses_for_all_users_and_semesters()
    clear_user_weakest_link_states()
    WeakestLinkProblem.objects.all().delete()
    WeakestLinkTopic.objects.all().delete()


def reset_semesters_without_disenroll():
    """Сбрасывает все пользовательские данные, созданные в процессе
    прохождения курсов без удаления данных о курсах.
    """
    delete_and_clear_all_objects()


def delete_everything():
    """Удаляет все объекты, связанные с курсами."""
    Course.objects.all().delete()
    User.objects.all().delete()


def disenroll_student(username: str, course_title: str):
    """Удаляет студента из курса."""
    user = User.objects.filter(username=username).first()
    semester = Semester.objects.filter(course__title=course_title).first()
    if user is None or semester is None:
        return
    Progress.objects.filter(user=user).delete()
    UserWeakestLinkState.objects.filter(user=user).delete()
    semester.students.remove(user)
