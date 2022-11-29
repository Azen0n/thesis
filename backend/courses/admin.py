from django.contrib import admin

import courses.models as courses_models
import answers.models as answers_models

courses = [courses_models.Course,
           courses_models.Module,
           courses_models.Topic,
           courses_models.Attachment,
           courses_models.Problem,
           courses_models.Hint]

answers = [answers_models.MultipleChoiceRadio,
           answers_models.MultipleChoiceCheckbox,
           answers_models.FillInSingleBlank,
           answers_models.FillInSingleBlankOption,
           answers_models.FillInMultipleBlanks,
           answers_models.FillInMultipleBlanksOption]

admin.site.register(courses)
admin.site.register(answers)
