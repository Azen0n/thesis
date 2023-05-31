from django.urls import path

from algorithm.views import (enroll_semester, next_theory_problem,
                             next_practice_problem, skip_theory_problem,
                             skip_practice_problem)

urlpatterns = [
    path('semesters/<uuid:pk>/enroll/', enroll_semester, name='enroll'),
    path('semesters/<uuid:semester_pk>/topics/<uuid:topic_pk>/next_theory_problem',
         next_theory_problem, name='next_theory_problem'),
    path('semesters/<uuid:semester_pk>/next_practice_problem',
         next_practice_problem, name='next_practice_problem'),
    path('semesters/<uuid:semester_pk>/problems/<uuid:problem_pk>/skip_theory_problem',
         skip_theory_problem, name='skip_theory_problem'),
    path('semesters/<uuid:semester_pk>/problems/<uuid:problem_pk>/skip_practice_problem',
         skip_practice_problem, name='skip_practice_problem'),
]
