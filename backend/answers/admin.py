from django.contrib import admin

import answers.models as answers_models

answers = [answers_models.MultipleChoiceRadio,
           answers_models.MultipleChoiceCheckbox,
           answers_models.FillInSingleBlank,
           answers_models.Code,
           answers_models.CodeAnswer,
           answers_models.Answer]

admin.site.register(answers)
