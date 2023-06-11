import time
from datetime import datetime
import json
from uuid import UUID

from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from algorithm.models import UserAnswer, Progress, TargetPoints, UserTargetPoints
from config.settings import Constants
from algorithm.pattern_simulator.patterns import (
    Pattern, Style, motivation_decay_generator, motivation_spikes_generator,
    falling_behind_generator, excessive_perfectionism_generator
)
from algorithm.pattern_simulator.pattern_simulator import PatternSimulator
from .models import Semester, Topic, Problem, THEORY_TYPES, PRACTICE_TYPES, SemesterCode
from answers.utils import get_answer_safe_data, get_correct_answers
from .utils import (is_problem_topic_completed, generate_join_code,
                    get_annotated_semester_topics, get_semester_code_context,
                    is_parent_topic_theory_low_reached, get_first_test)


class SemesterListView(ListView):
    model = Semester
    template_name = 'semesters.html'
    context_object_name = 'semesters'


class SemesterView(View):

    def get(self, request: HttpRequest, pk: UUID) -> HttpResponse:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Войдите в систему, чтобы просматривать курсы.'},
                          status=401)
        semester = Semester.objects.get(pk=pk)
        topics = get_annotated_semester_topics(request.user, semester)
        context = {
            'semester': semester,
            'topics': topics,
            'is_semester_teacher': request.user in semester.teachers.all(),
            'target_points_options': TargetPoints.choices,
            'is_enrolled': request.user in semester.students.all(),
        }
        context.update(get_semester_code_context(semester))
        return render(request, 'semester.html', context)


class TopicView(View):

    def get(self, request: HttpRequest, semester_pk: UUID, pk: UUID) -> HttpResponse:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Войдите в систему, чтобы просматривать темы.'},
                          status=401)
        semester = Semester.objects.get(pk=semester_pk)
        is_teacher = request.user in semester.teachers.all()
        if request.user not in semester.students.all() and not is_teacher:
            return render(request, 'error.html', {'message': 'Запишитесь на курс, чтобы просматривать темы.'})
        topic = Topic.objects.get(pk=pk)
        if not is_parent_topic_theory_low_reached(request.user, semester, topic):
            return render(request, 'error.html', {'message': f'Необходимо завершить тест по предыдущей теме.'},
                          status=401)
        theory_problems = Problem.objects.filter(main_topic=topic, type__in=THEORY_TYPES)
        practice_problems = Problem.objects.filter(main_topic=topic, type__in=PRACTICE_TYPES)
        context = {
            'is_teacher': is_teacher,
            'semester': semester,
            'topic': topic,
            'theory_problems': theory_problems,
            'practice_problems': practice_problems,
        }
        if not is_teacher:
            progress = Progress.objects.get(semester=semester, user=request.user, topic=topic)
            total_points = progress.theory_points + progress.practice_points
            max_points = Constants.TOPIC_THEORY_MAX_POINTS + Constants.TOPIC_PRACTICE_MAX_POINTS
            context.update({
                'theory_points': progress.theory_points,
                'practice_points': progress.practice_points,
                'total_points': total_points,
                'progress_percent': int(total_points / max_points * 100),
            })
        return render(request, 'topic.html', context)


class ProblemView(View):

    def get(self, request: HttpRequest, semester_pk: UUID, pk: UUID) -> HttpResponse:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Войдите в систему, чтобы просматривать задания.'},
                          status=401)
        semester = Semester.objects.get(pk=semester_pk)
        is_teacher = request.user in semester.teachers.all()
        if request.user not in semester.students.all() and not is_teacher:
            return render(request, 'error.html', {'message': 'Запишитесь на курс, чтобы просматривать задания.'})
        problem = Problem.objects.get(pk=pk)
        answer = get_answer_safe_data(problem)
        context = {
            'is_teacher': is_teacher,
            'semester': semester,
            'problem': problem,
            'is_practice_problem': problem.type in PRACTICE_TYPES,
            'answer': json.dumps(answer),
            'correct_answers': json.dumps(get_correct_answers(problem.id)),
        }
        if not is_teacher:
            progress = Progress.objects.get(user=request.user, semester=semester, topic=problem.main_topic)
            if problem.type in PRACTICE_TYPES and not progress.is_theory_low_reached():
                return render(request, 'error.html', {'message': 'Тест по теории не завершен.'})
            is_answered = UserAnswer.objects.filter(user=request.user, semester=semester, problem=problem).exists()
            is_topic_completed = is_problem_topic_completed(request.user, semester, problem)
            test_example = get_first_test(problem)
            context.update({
                'is_answered': is_answered,
                'is_topic_completed': is_topic_completed,
                'test_example': test_example,
            })
        return render(request, 'problem.html', context)


def generate_semester_code(request: HttpRequest, semester_pk: UUID) -> HttpResponse:
    """Создает новый код для присоединения к курсу."""
    if not request.user.is_authenticated:
        return render(request, 'error.html', {'message': 'Войдите в систему.'}, status=401)
    teacher = User.objects.get(id=request.user.pk)
    semester = Semester.objects.get(id=semester_pk)
    if teacher not in semester.teachers.all():
        return render(request, 'error.html', {'message': 'Вы не являетесь преподавателем курса.'},
                      status=403)
    expiration_time = datetime.strptime(json.loads(request.body)['expiration_time'], '%Y-%m-%dT%H:%M')
    code, created = SemesterCode.objects.update_or_create(
        semester=semester, defaults={
            'teacher': teacher,
            'code': generate_join_code(),
            'expired_at': timezone.make_aware(expiration_time)
        }
    )
    is_code_expired = code.expired_at < timezone.now()
    return JsonResponse(json.dumps({'code': code.code, 'is_code_expired': is_code_expired}), safe=False)


def change_target_points(request: HttpRequest) -> JsonResponse:
    """Изменяет баллы, к которым стремится алгоритм подбора заданий."""
    user_target_points = UserTargetPoints.objects.get_or_create(user=request.user)[0]
    points = json.loads(request.body).get('points', '')
    if points.isnumeric():
        points = int(points)
    try:
        user_target_points.target_points = TargetPoints(points)
        user_target_points.save()
        return JsonResponse(json.dumps({'status': '200'}), safe=False)
    except ValueError:
        return JsonResponse(json.dumps({'status': '422'}), safe=False)


def debug_pattern_simulator(request: HttpRequest):
    """Симуляция прохождения курса студентами н основе четырех паттернов:
    1. «Снижение мотивации со временем»
    2. «Периодические всплески мотивации»
    3. «Отставание»
    4. «Излишний перфекционизм»
    """
    target_points_list: list[TargetPoints] = [
        TargetPoints.LOW,
        TargetPoints.MEDIUM,
        TargetPoints.HIGH
    ]
    pattern_generators = [
        motivation_decay_generator,
        motivation_spikes_generator,
        falling_behind_generator,
        excessive_perfectionism_generator
    ]
    times = []
    for target_points in target_points_list:
        for generator in pattern_generators:
            s = time.time()
            pattern = Pattern(target_points=target_points,
                              style=Style.THEORY_FIRST,
                              generator=generator)
            simulator = PatternSimulator(pattern)
            simulator.run()
            e = time.time()
            times.append((e - s) / 60)
    return JsonResponse(json.dumps({'status': '200', 'times': times}), safe=False)
