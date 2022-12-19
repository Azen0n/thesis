from django.urls import path

from courses.views import (SemesterListView, SemesterDetailView,
                           TopicDetailView, ProblemView)

urlpatterns = [
    path('semesters/', SemesterListView.as_view(), name='semesters'),
    path('semesters/<uuid:pk>/', SemesterDetailView.as_view(), name='semester'),
    path('topics/<uuid:pk>/', TopicDetailView.as_view(), name='topic'),
    path('problems/<uuid:pk>/', ProblemView.as_view(), name='problem'),
]
