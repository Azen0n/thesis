import uuid

from django.db import models

from courses.models import Problem


class MultipleChoiceRadio(models.Model):
    """Multiple Choice Radio Type of Problem model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    is_correct = models.BooleanField()
    explanation = models.TextField(null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class MultipleChoiceCheckbox(models.Model):
    """Multiple Choice Checkbox Type of Problem model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    is_correct = models.BooleanField()
    explanation = models.TextField(null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class FillInSingleBlank(models.Model):
    """Fill In Single Blank Type of Problem model.
    Each entry is correct variant of answer.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    explanation = models.TextField(null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class Answer(models.Model):
    """Сущность, содержащая ответ пользователя на задание конкретного типа."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    multiple_choice_radio = models.ForeignKey(MultipleChoiceRadio,
                                              on_delete=models.CASCADE,
                                              blank=True, null=True)
    multiple_choice_checkbox = models.ForeignKey(MultipleChoiceCheckbox,
                                                 on_delete=models.CASCADE,
                                                 blank=True, null=True)
    fill_in_single_blank = models.ForeignKey(FillInSingleBlank,
                                             on_delete=models.CASCADE,
                                             blank=True, null=True)
