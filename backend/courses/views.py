import json
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

from algorithm.models import UserAnswer, Progress
from .models import Semester, Topic, Problem
from answers.utils import get_answer_safe_data


class SemesterListView(ListView):
    model = Semester
    template_name = 'semesters.html'
    context_object_name = 'semesters'


class SemesterView(View):

    def get(self, request: HttpRequest, pk: UUID):
        semester = Semester.objects.get(pk=pk)
        context = {
            'semester': semester,
        }
        return render(request, 'semester.html', context)


class TopicView(View):

    def get(self, request: HttpRequest, semester_pk: UUID, pk: UUID):
        semester = Semester.objects.get(pk=semester_pk)
        topic = Topic.objects.get(pk=pk)
        progress = Progress.objects.get(semester=semester, user=request.user, topic__id=pk)
        context = {
            'semester': semester,
            'topic': topic,
            'theory_points': progress.theory_points,
            'practice_points': progress.practice_points,
        }
        return render(request, 'topic.html', context)


class ProblemView(View):

    def get(self, request: HttpRequest, semester_pk: UUID, pk: UUID):
        semester = Semester.objects.get(pk=semester_pk)
        problem = Problem.objects.get(pk=pk)
        answer = get_answer_safe_data(problem)
        is_answered = UserAnswer.objects.filter(
            user=request.user,
            semester=semester,
            problem=problem
        ).exists()
        context = {
            'semester': semester,
            'problem': problem,
            'is_answered': is_answered,
            'answer': json.dumps(answer),
        }
        return render(request, 'problem.html', context)
