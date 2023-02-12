from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from answers.models import Answer
from courses.models import Topic, Problem, Difficulty, Semester


class AbstractProgress(models.Model):
    points = models.FloatField(default=0)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @property
    def max(self):
        return self.topic.module.course.topic_max_points

    def is_low_reached(self) -> bool:
        topic_max_points = self.topic.module.course.topic_max_points
        threshold_low = self.topic.module.course.topic_threshold_low
        low = self.max * (threshold_low / topic_max_points)
        return self.points >= low

    def is_medium_reached(self) -> bool:
        topic_max_points = self.topic.module.course.topic_max_points
        threshold_medium = self.topic.module.course.topic_threshold_medium
        medium = self.max * (threshold_medium / topic_max_points)
        return self.points >= medium

    def is_high_reached(self) -> bool:
        topic_max_points = self.topic.module.course.topic_max_points
        threshold_high = self.topic.module.course.topic_threshold_high
        high = self.max * (threshold_high / topic_max_points)
        return self.points >= high

    def is_completed(self) -> bool:
        return self.points >= self.max

    def __str__(self):
        return f'{self.topic.title} ({self.points:.2f})'


class TheoryProgress(AbstractProgress):

    @property
    def max(self):
        return self.topic.module.course.topic_theory_max_points


class PracticeProgress(AbstractProgress):

    @property
    def max(self):
        return self.topic.module.course.topic_practice_max_points


class WeakestLinkProblem(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    progress = models.ForeignKey('Progress', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class WeakestLinkTopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    progress = models.ForeignKey('Progress', on_delete=models.CASCADE)


class Progress(models.Model):
    class WeakestLinkState(models.TextChoices):
        FALSE = 'False', _('Weakest Link in process')
        TRUE = 'True', _('Weakest Link done')
        NONE = 'None', _('Weakest Link not started')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    theory = models.ForeignKey(TheoryProgress, on_delete=models.CASCADE)
    practice = models.ForeignKey(PracticeProgress, on_delete=models.CASCADE)
    weakest_link_state = models.CharField(max_length=5,
                                          choices=WeakestLinkState.choices,
                                          default=WeakestLinkState.NONE)

    @property
    def points(self) -> float:
        return self.theory.points + self.practice.points

    def __str__(self):
        return (f'{self.user.username} - {self.topic.title}'
                f' ({self.theory.points:.2f} / {self.practice.points:.2f}'
                f' / {self.theory.points + self.practice.points:.2f})')


class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    is_solved = models.BooleanField()
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class UserCurrentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    progress = models.ForeignKey(Progress, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user', 'semester'),)
