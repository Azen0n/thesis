from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from algorithm.utils import create_user_progress
from courses.models import Semester


def enroll_semester(request: HttpRequest, pk: UUID) -> HttpResponse:
    semester = Semester.objects.get(pk=pk)
    if semester.students.filter(pk=request.user.pk).first() is None:
        semester.students.add(request.user)
        create_user_progress(semester, request.user)
    return redirect(f'/semesters/{semester.pk}')
