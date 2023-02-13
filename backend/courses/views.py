import json
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView

from .models import Semester, Topic, Problem
from .utils import get_answer_safe_data


class SemesterListView(ListView):
    model = Semester
    template_name = 'semesters.html'
    context_object_name = 'semesters'


class SemesterDetailView(DetailView):
    model = Semester
    template_name = 'semester.html'
    context_object_name = 'semester'


class TopicView(View):

    def get(self, request: HttpRequest, semester_pk: UUID, pk: UUID):
        semester = Semester.objects.get(pk=semester_pk)
        topic = Topic.objects.get(pk=pk)
        context = {
            'semester': semester,
            'topic': topic,
        }
        return render(request, 'topic.html', context)


class ProblemView(View):

    def get(self, request: HttpRequest, semester_pk: UUID, pk: UUID):
        semester = Semester.objects.get(pk=semester_pk)
        problem = Problem.objects.get(pk=pk)
        answer = get_answer_safe_data(problem)
        context = {
            'semester': semester,
            'problem': problem,
            'answer': json.dumps(answer),
        }
        return render(request, 'problem.html', context)
