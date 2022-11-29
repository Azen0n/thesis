from django.views.generic import ListView, DetailView

from .models import Semester, Topic


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
