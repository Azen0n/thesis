from dataclasses import dataclass

from django.db.models import QuerySet

from algorithm.models import UserCurrentProgress
from courses.models import Problem, Type


@dataclass
class PracticeSelector:

    @property
    def problems(self) -> QuerySet[Problem]:
        """Возвращает теоретические задания."""
        return Problem.objects.filter(type__in=[

        ])

    def next(self, u: UserCurrentProgress) -> Problem:
        """Возвращает практическое задание по текущей теме пользователя."""
        ...
