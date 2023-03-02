import json
from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

from algorithm.models import UserAnswer, Progress
from .models import Semester, Topic, Problem, PRACTICE_TYPES
from answers.utils import get_answer_safe_data
from .utils import is_problem_topic_completed


class SemesterListView(ListView):
    model = Semester
    template_name = 'semesters.html'
    context_object_name = 'semesters'


class SemesterView(View):

    def get(self, request: HttpRequest, pk: UUID):
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Войдите в систему, чтобы просматривать курсы.'},
                          status=401)
        semester = Semester.objects.get(pk=pk)
        context = {
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

    def get(self, request: HttpRequest, semester_pk: UUID, pk: UUID):
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Войдите в систему, чтобы просматривать темы.'},
                          status=401)
        semester = Semester.objects.get(pk=semester_pk)
        topic = Topic.objects.get(pk=pk)
        parent_topic_progress = Progress.objects.filter(semester=semester, user=request.user,
                                                        topic=topic.parent_topic).first()
        if parent_topic_progress is not None:
            if not parent_topic_progress.is_theory_low_reached():
                return render(request, 'error.html', {'message': f'Необходимо завершить тест по теории по теме'
                                                                 f' {parent_topic_progress.topic}.'})
        progress = Progress.objects.get(semester=semester, user=request.user, topic=topic)
        context = {
            'semester': semester,
            'topic': topic,
            'theory_points': progress.theory_points,
            'practice_points': progress.practice_points,
        }
        return render(request, 'topic.html', context)


class ProblemView(View):

    def get(self, request: HttpRequest, semester_pk: UUID, pk: UUID):
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Войдите в систему, чтобы просматривать задания.'},
                          status=401)
        semester = Semester.objects.get(pk=semester_pk)
        problem = Problem.objects.get(pk=pk)
        progress = Progress.objects.get(user=request.user, semester=semester, topic=problem.main_topic)
        if problem.type in PRACTICE_TYPES and not progress.is_theory_low_reached():
            return render(request, 'error.html', {'message': 'Тест по теории не завершен.'})
        answer = get_answer_safe_data(problem)
        is_answered = UserAnswer.objects.filter(
            user=request.user,
            semester=semester,
            problem=problem
        ).exists()
        is_topic_completed = is_problem_topic_completed(request.user, semester, problem)
        context = {
            'semester': semester,
            'problem': problem,
            'is_answered': is_answered,
            'is_topic_completed': is_topic_completed,
            'answer': json.dumps(answer),
        }
        return render(request, 'problem.html', context)
