import uuid

from django.db import models


class Course(models.Model):
    """Base Course model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    description = models.TextField()
    duration = models.IntegerField()
    thumbnail = models.FileField(upload_to='thumbnails/')

    def __str__(self):
        return self.title


class Module(models.Model):
    """Course Module model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    description = models.TextField()
    is_required = models.BooleanField(default=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Topic(models.Model):
    """Module Topic model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    time_to_complete = models.IntegerField()
    is_required = models.BooleanField(default=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Attachment(models.Model):
    """Topic Attachment model."""
    url = models.TextField(primary_key=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    def __str__(self):
        return self.url


class Problem(models.Model):
    """Topic Problem model."""

    class Type(models.TextChoices):
        """Each Problem type has a separate table."""
        MULTIPLE_CHOICE_RADIO = 'Multiple Choice Radio'
        MULTIPLE_CHOICE_CHECKBOX = 'Multiple Choice Checkbox'
        FILL_IN_SINGLE_BLANK = 'Fill In Single Blank'
        FILL_IN_MULTIPLE_BLANKS = 'Fill In Multiple Blanks'
        ESSAY = 'Essay'

    class Difficulty(models.IntegerChoices):
        """Problem Difficulty."""
        EASY = 1
        NORMAL = 2
        HARD = 3

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    description = models.TextField()
    type = models.CharField(max_length=100, choices=Type.choices)
    difficulty = models.IntegerField(choices=Difficulty.choices)
    value = models.IntegerField()
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Hint(models.Model):
    """Problem Hint model."""

    class Cost(models.IntegerChoices):
        """Hint Cost is by how many points the value of the Problem will be reduced."""
        SMALL = 1
        MEDIUM = 2
        LARGE = 3

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
