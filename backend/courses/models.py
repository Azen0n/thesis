from __future__ import annotations
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    """Base Course model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    description = models.TextField()
    duration = models.IntegerField()
    thumbnail = models.FileField(upload_to='thumbnails/', blank=True, null=True)

    topic_threshold_low = models.IntegerField(default=61)
    topic_threshold_medium = models.IntegerField(default=76)
    topic_threshold_high = models.IntegerField(default=91)
    topic_theory_max_points = models.IntegerField(default=40)
    topic_practice_max_points = models.IntegerField(default=60)

    points_easy = models.IntegerField(default=2)
    points_normal = models.IntegerField(default=5)
    points_hard = models.IntegerField(default=9)

    difficulty_threshold_normal = models.IntegerField(default=3)
    difficulty_threshold_hard = models.IntegerField(default=2)

    sub_topic_points_coefficient = models.FloatField(default=1 / 3)

    @property
    def topic_max_points(self) -> float:
        return self.topic_theory_max_points + self.topic_practice_max_points

    def __str__(self):
        return self.title


class Semester(models.Model):
    """Semester model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    students = models.ManyToManyField(User, related_name='semester_student_set')
    teachers = models.ManyToManyField(User, related_name='semester_teacher_set')

    def __str__(self):
        return f'{self.course}, {self.started_at.strftime("%m.%Y")} - {self.ended_at.strftime("%m.%Y")}'


class Module(models.Model):
    """Course Module model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    description = models.TextField()
    is_required = models.BooleanField(default=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    @property
    def problem_count(self):
        return Problem.objects.filter(main_topic__module=self.pk).count()

    @property
    def total_time(self):
        return Topic.objects.filter(module=self.pk).aggregate(Sum('time_to_complete'))['time_to_complete__sum']


class Topic(models.Model):
    """Module Topic model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    time_to_complete = models.IntegerField()
    is_required = models.BooleanField(default=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    @property
    def next(self):
        return Topic.objects.filter()


class Attachment(models.Model):
    """Topic Attachment model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    url = models.TextField()
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Difficulty(models.IntegerChoices):
    """Problem Difficulty."""
    EASY = 1, _('Легкое')
    NORMAL = 2, _('Нормальное')
    HARD = 3, _('Сложное')


class Type(models.TextChoices):
    """Each Problem type has a separate table."""
    MULTIPLE_CHOICE_RADIO = 'Multiple Choice Radio', _('Выбор одного варианта')
    MULTIPLE_CHOICE_CHECKBOX = 'Multiple Choice Checkbox', _('Выбор нескольких вариантов')
    FILL_IN_SINGLE_BLANK = 'Fill In Single Blank', _('Заполнение пропуска')


class Problem(models.Model):
    """Topic Problem model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    description = models.TextField()
    type = models.CharField(max_length=100, choices=Type.choices)
    difficulty = models.IntegerField(choices=Difficulty.choices)
    main_topic = models.ForeignKey(Topic, on_delete=models.CASCADE,
                                   related_name='problem_main_set')
    sub_topics = models.ManyToManyField(Topic, related_name='problem_sub_set',
                                        blank=True)

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

    def __str__(self):
        return self.text
