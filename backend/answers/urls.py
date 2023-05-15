from django.urls import path

from answers.views import validate_answer, run_stdin

urlpatterns = [
    path('semesters/<uuid:semester_pk>/problems/<uuid:problem_pk>/validate_answer/',
         validate_answer, name='validate_answer'),
    path('semesters/<uuid:semester_pk>/problems/<uuid:problem_pk>/run_stdin/',
         run_stdin, name='run_stdin'),
]
