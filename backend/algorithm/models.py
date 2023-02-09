from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

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
        low = topic_max_points * (threshold_low / self.max)
        return self.points >= low

    def is_medium_reached(self) -> bool:
        topic_max_points = self.topic.module.course.topic_max_points
        threshold_medium = self.topic.module.course.topic_threshold_medium
        medium = topic_max_points * (threshold_medium / self.max)
        return self.points >= medium

    def is_high_reached(self) -> bool:
        topic_max_points = self.topic.module.course.topic_max_points
        threshold_high = self.topic.module.course.topic_threshold_high
        high = topic_max_points * (threshold_high / self.max)
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

    @property
    def practice_difficulty(self) -> dict[Difficulty, int]:
        normal = self.topic.module.course.difficulty_threshold_normal
        hard = self.topic.module.course.difficulty_threshold_hard
        is_medium_reached = self.theory.is_medium_reached()
        is_high_reached = self.theory.is_high_reached()

        return {
            Difficulty.EASY: normal if is_medium_reached else 0,
            Difficulty.NORMAL: hard if is_high_reached else 0,
            Difficulty.HARD: 0
        }

    @property
    def max_difficulty(self) -> Difficulty:
        normal = self.topic.module.course.difficulty_threshold_normal
        hard = self.topic.module.course.difficulty_threshold_hard

        if self.theory.is_high_reached():
            return Difficulty.HARD
        if self.practice_difficulty[Difficulty.NORMAL] >= hard:
            return Difficulty.HARD
        if self.theory.is_medium_reached():
            return Difficulty.NORMAL
        if self.practice_difficulty[Difficulty.EASY] >= normal:
            return Difficulty.NORMAL
        return Difficulty.EASY

    def __str__(self):
        return (f'{self.user.username} - {self.topic.title}'
                f' ({self.theory.points:.2f} / {self.practice.points:.2f}'
                f' / {self.theory.points + self.practice.points:.2f})')


class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    is_solved = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)


class UserCurrentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    progress = models.ForeignKey(Progress, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user', 'semester'),)
