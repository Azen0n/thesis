from uuid import UUID

from django.contrib.auth.models import User

from algorithm.models import Progress, TheoryProgress, PracticeProgress, UserCurrentProgress
from algorithm.problem_selector import ProblemSelector
from courses.models import Semester, Topic


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
            theory_progress = TheoryProgress.objects.create(topic=topic)
            practice_progress = PracticeProgress.objects.create(topic=topic)
            Progress.objects.create(user=user,
                                    semester=semester,
                                    topic=topic,
                                    theory=theory_progress,
                                    practice=practice_progress)


def find_user_current_progress(user: User, semester_pk: UUID,
                               topic_pk: UUID) -> UserCurrentProgress:
    """Возвращает прогресс пользователя по теме, устанавливая ее как текущую."""
    topic = Topic.objects.get(pk=topic_pk)
    progress = Progress.objects.get(user=user, topic=topic, semester__id=semester_pk)
    current_topic = UserCurrentProgress.objects.get(user=user, semester=progress.semester)
    current_topic.progress = progress
    current_topic.save()
    return current_topic
