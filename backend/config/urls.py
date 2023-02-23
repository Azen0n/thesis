from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('courses.urls')),
    path('', include('accounts.urls')),
    path('', include('algorithm.urls')),
    path('', include('answers.urls')),
]
