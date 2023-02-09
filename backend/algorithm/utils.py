from django.contrib.auth.models import User

from algorithm.models import Progress, TheoryProgress, PracticeProgress
from algorithm.problem_selector import ProblemSelector
from courses.models import Semester, Topic, Problem, Type


def initialize_algorithm() -> ProblemSelector:
    theory_problems = []
    practice_problems = []
    return ProblemSelector(theory_problems, practice_problems)


def create_user_progress(semester: Semester, user: User):
    """Создает прогресс каждой темы курса семестра."""
    for module in semester.course.module_set.all():
        for topic in module.topic_set.all():
            progress = get_progress_or_none(topic, user)
            if progress:
                continue
            theory_progress = TheoryProgress.objects.create(topic=topic)
            practice_progress = PracticeProgress.objects.create(topic=topic)
            Progress.objects.create(user=user, topic=topic,
                                    theory=theory_progress,
                                    practice=practice_progress)


def get_progress_or_none(topic: Topic, user: User) -> Progress | None:
    return Progress.objects.filter(topic=topic, user=user).first()
