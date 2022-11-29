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

    Answer (text) format is "The Mona Lisa was painted by Leonardo {1}." where
    input is located in curly braces. If text is null, then input is displayed
    without additional text.
    Blank has one or more accepted options.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField(null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class FillInSingleBlankOption(models.Model):
    """Option for Fill In Single Blank Type."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    answer = models.ForeignKey(FillInSingleBlank, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text


class FillInMultipleBlanks(models.Model):
    """Fill In Multiple Blanks Type of Problem model.

    Answer (text) format is "The Mona {0} was painted by Leonardo {1}." where
    inputs are located in curly braces.
    Each blank has one or more accepted options.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    explanation = models.TextField(null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class FillInMultipleBlanksOption(models.Model):
    """Option for Fill In Multiple Blank Type."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    answer = models.ForeignKey(FillInMultipleBlanks, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text
