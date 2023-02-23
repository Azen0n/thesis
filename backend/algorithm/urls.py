from django.urls import path

from algorithm.views import enroll_semester

urlpatterns = [
    path('enroll/<uuid:semester_pk>/', enroll_semester, name='enroll'),
]
