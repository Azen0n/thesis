import uuid

from django.db import models

from courses.models import Problem


class AbstractAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    explanation = models.TextField(null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class MultipleChoiceRadio(AbstractAnswer):
    """Задание на выбор одного варианта ответа (radio button)."""
    is_correct = models.BooleanField()

    def __str__(self):
        return self.text


class MultipleChoiceCheckbox(AbstractAnswer):
    """Задание на выбор нескольких вариантов ответа (checkbox)."""
    is_correct = models.BooleanField()

    def __str__(self):
        return self.text


class FillInSingleBlank(AbstractAnswer):
    """Задание на заполнение пропуска (произвольный ответ). Каждая запись
    представляет собой один из корректных вариантов ответа.
    """

    def __str__(self):
        return self.text


class Answer(models.Model):
    """Сущность, содержащая ответ пользователя на задание конкретного типа."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_answer = models.ForeignKey('algorithm.UserAnswer', on_delete=models.CASCADE)
    multiple_choice_radio = models.ForeignKey(MultipleChoiceRadio,
                                              on_delete=models.CASCADE,
                                              blank=True, null=True)
    multiple_choice_checkbox = models.ForeignKey(MultipleChoiceCheckbox,
                                                 on_delete=models.CASCADE,
                                                 blank=True, null=True)
    fill_in_single_blank = models.TextField(blank=True, null=True)

    def __str__(self):
        answer = ''
        if self.multiple_choice_radio is not None:
            answer = f'multiple_choice_radio={self.multiple_choice_radio}'
        elif self.multiple_choice_checkbox is not None:
            answer = f'multiple_choice_checkbox={self.multiple_choice_checkbox}'
        elif self.fill_in_single_blank is not None:
            answer = f'fill_in_single_blank={self.fill_in_single_blank}'
        return (f'user_answer={self.user_answer},'
                f' {answer}')
