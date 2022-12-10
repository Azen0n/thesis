from django.contrib import admin

import answers.models as answers_models

answers = [answers_models.MultipleChoiceRadio,
           answers_models.MultipleChoiceCheckbox,
           answers_models.FillInSingleBlank,
           answers_models.FillInSingleBlankOption]

admin.site.register(answers)
