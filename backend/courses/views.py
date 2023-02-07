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


class TopicDetailView(DetailView):
    model = Topic
    template_name = 'topic.html'
    context_object_name = 'topic'


class ProblemDetailView(DetailView):
    model = Problem
    template_name = 'problem.html'
    context_object_name = 'problem'


class ProblemView(View):

    def get(self, request: HttpRequest, pk: UUID):
        problem = Problem.objects.get(pk=pk)
        answer = get_answer_safe_data(problem)
        context = {
            'problem': problem,
            'answer': json.dumps(answer),
        }
        return render(request, 'problem.html', context)
