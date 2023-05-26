from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('courses.urls')),
    path('', include('accounts.urls')),
    path('', include('algorithm.urls')),
    path('', include('answers.urls')),
    path('', RedirectView.as_view(pattern_name='semesters', permanent=False))
]
