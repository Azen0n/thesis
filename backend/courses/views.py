from datetime import datetime
import json
from uuid import UUID

from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from algorithm.models import UserAnswer, Progress
from .models import Semester, Topic, Problem, PRACTICE_TYPES, SemesterCode
from answers.utils import get_answer_safe_data, get_correct_answers
from .utils import is_problem_topic_completed, generate_join_code


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
        code = SemesterCode.objects.filter(semester=semester).first()
        code = '' if code is None else code
        is_code_expired = code.expired_at < timezone.now()
        default_expiration_time = timezone.now() + timezone.timedelta(weeks=1)
        if default_expiration_time > semester.ended_at:
            default_expiration_time = timezone.now()
        context = {
            'is_teacher': semester in request.user.semester_teacher_set.all(),
            'is_student': semester in request.user.semester_student_set.all(),
            'code': code,
            'is_code_expired': is_code_expired,
            'min_expiration_time': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'max_expiration_time': semester.ended_at.strftime('%Y-%m-%dT%H:%M'),
            'default_expiration_time': default_expiration_time.strftime('%Y-%m-%dT%H:%M'),
            'semester': semester,
            'modules': [{
                'module': module,
                'topics': [{
                    'topic': topic,
                    'progress': Progress.objects.filter(
                        user=request.user,
                        semester=semester,
                        topic=topic
                    ).first()
                } for topic in module.topic_set.all()]
            } for module in semester.course.module_set.all()]
        }
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
        if not is_teacher:
            parent_topic_progress = Progress.objects.filter(semester=semester, user=request.user,
                                                            topic=topic.parent_topic).first()
            if parent_topic_progress is not None:
                if not parent_topic_progress.is_theory_low_reached():
                    return render(request, 'error.html', {'message': f'Необходимо завершить тест по теории по теме'
                                                                     f' {parent_topic_progress.topic}.'})
            progress = Progress.objects.get(semester=semester, user=request.user, topic=topic)
            context = {
                'is_teacher': is_teacher,
                'semester': semester,
                'topic': topic,
                'theory_points': progress.theory_points,
                'practice_points': progress.practice_points,
            }
        else:
            context = {
                'is_teacher': is_teacher,
                'semester': semester,
                'topic': topic,
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
        if not is_teacher:
            progress = Progress.objects.get(user=request.user, semester=semester, topic=problem.main_topic)
            if problem.type in PRACTICE_TYPES and not progress.is_theory_low_reached():
                return render(request, 'error.html', {'message': 'Тест по теории не завершен.'})
            is_answered = UserAnswer.objects.filter(
                user=request.user,
                semester=semester,
                problem=problem
            ).exists()
            is_topic_completed = is_problem_topic_completed(request.user, semester, problem)
            context = {
                'is_teacher': is_teacher,
                'semester': semester,
                'problem': problem,
                'is_answered': is_answered,
                'is_topic_completed': is_topic_completed,
                'answer': json.dumps(answer),
                'is_practice_problem': problem.type in PRACTICE_TYPES,
            }
        else:
            context = {
                'is_teacher': is_teacher,
                'semester': semester,
                'problem': problem,
                'answer': json.dumps(answer),
                'correct_answers': json.dumps(get_correct_answers(problem.id))
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
