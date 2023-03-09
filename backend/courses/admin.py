from django.contrib import admin

import courses.models as courses_models

courses = [courses_models.Course,
           courses_models.Semester,
           courses_models.Module,
           courses_models.Topic,
           courses_models.Attachment,
           courses_models.Problem,
           courses_models.Hint,
           courses_models.SemesterCode]

admin.site.register(courses)
