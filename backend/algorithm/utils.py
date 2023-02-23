from django.contrib.auth.models import User

from algorithm.models import Progress, UserWeakestLinkState, WeakestLinkState
from algorithm.problem_selector import ProblemSelector
from courses.models import Semester


def initialize_algorithm() -> ProblemSelector:
    return ProblemSelector()


def create_user_progress(semester: Semester, user: User):
    """Создает прогресс каждой темы курса семестра."""
    for module in semester.course.module_set.all():
        for topic in module.topic_set.all():
            progress = Progress.objects.filter(user=user,
                                               semester=semester,
                                               topic=topic).first()
            if progress:
                continue
            Progress.objects.create(user=user, semester=semester, topic=topic)
    user_weakest_link_state = UserWeakestLinkState.objects.filter(
        user=user,
        semester=semester
    ).first()
    if user_weakest_link_state is None:
        UserWeakestLinkState.objects.create(user=user,
                                            semester=semester,
                                            state=WeakestLinkState.NONE)
