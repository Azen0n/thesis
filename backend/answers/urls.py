from django.urls import path

from answers.views import validate_answer

urlpatterns = [
    path('semesters/<uuid:semester_pk>/problems/<uuid:problem_pk>/validate_answer/',
         validate_answer, name='validate_answer'),
]
