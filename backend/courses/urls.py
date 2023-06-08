from django.urls import path

from courses.views import (SemesterListView, SemesterView,
                           TopicView, ProblemView, generate_semester_code,
                           debug_pattern_simulator, change_target_points)

urlpatterns = [
    path('semesters/', SemesterListView.as_view(), name='semesters'),
    path('semesters/<uuid:pk>/', SemesterView.as_view(), name='semester'),
    path('semesters/<uuid:semester_pk>/topics/<uuid:pk>/', TopicView.as_view(), name='topic'),
    path('semesters/<uuid:semester_pk>/problems/<uuid:pk>/', ProblemView.as_view(), name='problem'),
    path('semesters/<uuid:semester_pk>/generate_semester_code/', generate_semester_code, name='generate_semester_code'),
    path('debug/', debug_pattern_simulator, name='debug_pattern_simulator'),
    path('change_target_points/', change_target_points, name='change_target_points'),
]
