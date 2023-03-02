import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from answers.models import Answer
from config.settings import Constants
from courses.models import Topic, Problem, Semester, Course


class AbstractUserSemester(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Progress(AbstractUserSemester):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    theory_points = models.FloatField(default=0.0)
    practice_points = models.FloatField(default=0.0)
    skill_level = models.FloatField(default=1.4)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'semester', 'topic'],
                                    name='unique_user_semester_topic')
        ]

    @property
    def points(self) -> float:
        return self.theory_points + self.practice_points

    def is_theory_low_reached(self) -> bool:
        max_points = Constants.TOPIC_THEORY_MAX_POINTS + Constants.TOPIC_PRACTICE_MAX_POINTS
        theory_low_coefficient = Constants.TOPIC_THRESHOLD_LOW / max_points
        return self.theory_points >= Constants.TOPIC_THEORY_MAX_POINTS * theory_low_coefficient

    def is_theory_completed(self) -> bool:
        return self.theory_points >= Constants.TOPIC_THEORY_MAX_POINTS

    def is_practice_completed(self) -> bool:
        return self.practice_points >= Constants.TOPIC_PRACTICE_MAX_POINTS

    def __str__(self):
        return (f'{self.user.username} - {self.topic.title}'
                f' ({self.theory_points:.2f} / {self.practice_points:.2f}'
                f' / {self.theory_points + self.practice_points:.2f})')


class UserAnswer(AbstractUserSemester):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    is_solved = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f'user={self.user}, problem={self.problem},'
                f' is_solved={self.is_solved}')


class WeakestLinkTopic(AbstractUserSemester):
    """Темы проблемных заданий с указанием группы."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    group_number = models.IntegerField()

    def __str__(self):
        return (f'semester={self.semester}, topic={self.topic},'
                f' group_number={self.group_number}, user={self.user}')


class WeakestLinkProblem(AbstractUserSemester):
    """Задание из очереди слабого звена."""
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    group_number = models.IntegerField()
    is_solved = models.BooleanField(default=None, blank=True, null=True)

    def __str__(self):
        return (f'semester={self.semester}, problem={self.problem},'
                f' group_number={self.group_number}, user={self.user}')


class WeakestLinkState(models.TextChoices):
    """NONE — алгоритм подбора заданий работает в обычном режиме.
    IN_PROGRESS — алгоритм поиска слабого звена запущен, задания подбираются
    из очереди (WeakestLinkProblem).
    DONE — алгоритм поиска слабого звена завершен, необходимо провести
    перерасчет уровня знаний по темам.
    """
    NONE = 'None', _('Weakest Link not started')
    IN_PROGRESS = 'In progress', _('Weakest Link in progress')
    DONE = 'Done', _('Weakest Link done')


class UserWeakestLinkState(AbstractUserSemester):
    """Состояние алгоритма поиска слабого звена."""
    state = models.CharField(max_length=11,
                             choices=WeakestLinkState.choices,
                             default=WeakestLinkState.NONE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'semester'],
                                    name='unique_user_semester')
        ]

    def __str__(self):
        return (f'semester={self.semester}, user={self.user},'
                f' state={self.state}')


class TopicGraphEdge(models.Model):
    """Грани графа связи тем."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    topic1 = models.ForeignKey(Topic, on_delete=models.CASCADE,
                               related_name='topic_topicgraphedge_set1')
    topic2 = models.ForeignKey(Topic, on_delete=models.CASCADE,
                               related_name='topic_topicgraphedge_set2')
    weight = models.FloatField()

    def __str__(self):
        return f'{self.topic1} -> {self.topic2} ({self.weight})'
