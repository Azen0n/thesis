from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from algorithm.models import UserCurrentTopic
from algorithm.utils import create_user_progress, initialize_algorithm
from courses.models import Semester

algorithm = initialize_algorithm()


def enroll_semester(request: HttpRequest, pk: UUID) -> HttpResponse:
    semester = Semester.objects.get(pk=pk)
    if semester.students.filter(pk=request.user.pk).first() is None:
        semester.students.add(request.user)
        create_user_progress(semester, request.user)
    return redirect(f'/semesters/{semester.pk}')


def next_theory_problem(request: HttpRequest, pk: UUID) -> HttpResponse:
    semester = Semester.objects.get(pk=pk)
    current_topic = UserCurrentTopic.objects.get(user=request.user,
                                                 semester=semester)
    problem = algorithm.next_theory_problem(current_topic)
