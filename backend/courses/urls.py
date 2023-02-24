from django.urls import path

from courses.views import (SemesterListView, SemesterView,
                           TopicView, ProblemView)

urlpatterns = [
    path('semesters/', SemesterListView.as_view(), name='semesters'),
    path('semesters/<uuid:pk>/', SemesterView.as_view(), name='semester'),
    path('semesters/<uuid:semester_pk>/topics/<uuid:pk>/', TopicView.as_view(), name='topic'),
    path('semesters/<uuid:semester_pk>/problems/<uuid:pk>/', ProblemView.as_view(), name='problem'),
]
