from datetime import datetime
import json
from uuid import UUID

from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from algorithm.models import Progress, UserAnswer
from config.settings import Constants
from .models import Semester, Topic, Problem, PRACTICE_TYPES, SemesterCode, THEORY_TYPES
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
        progress = Progress.objects.get(semester=semester, user=request.user, topic=topic)
        theory_problems = Problem.objects.filter(main_topic=topic, type__in=THEORY_TYPES)
        practice_problems = Problem.objects.filter(main_topic=topic, type__in=PRACTICE_TYPES)
        total_points = progress.theory_points + progress.practice_points
        max_points = Constants.TOPIC_THEORY_MAX_POINTS + Constants.TOPIC_PRACTICE_MAX_POINTS
        context = {
            'is_teacher': is_teacher,
            'semester': semester,
            'topic': topic,
            'theory_problems': theory_problems,
            'practice_problems': practice_problems,
            'theory_points': progress.theory_points,
            'practice_points': progress.practice_points,
            'total_points': total_points,
            'progress_percent': int(total_points / max_points * 100)
        }
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
        progress = Progress.objects.get(user=request.user, semester=semester, topic=problem.main_topic)
        if problem.type in PRACTICE_TYPES and not progress.is_theory_low_reached():
            return render(request, 'error.html', {'message': 'Тест по теории не завершен.'})
        is_answered = UserAnswer.objects.filter(user=request.user, semester=semester, problem=problem).exists()
        is_topic_completed = is_problem_topic_completed(request.user, semester, problem)
        test_example = get_first_test(problem)
        context = {
            'is_teacher': is_teacher,
            'semester': semester,
            'problem': problem,
            'is_answered': is_answered,
            'is_practice_problem': problem.type in PRACTICE_TYPES,
            'answer': json.dumps(answer),
            'is_topic_completed': is_topic_completed,
            'correct_answers': json.dumps(get_correct_answers(problem.id)),
            'test_example': test_example,
        }
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
