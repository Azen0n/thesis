import logging

from django.contrib.auth.models import User

from algorithm.models import (Progress, UserWeakestLinkState, WeakestLinkState,
                              WeakestLinkProblem)
from config.settings import Constants
from courses.models import Problem, Semester
from .points_maximization import get_problems_with_max_value
from .utils import (filter_practice_problems, filter_theory_problems,
                    get_last_theory_user_answers, get_suitable_problem_difficulty)
from ..utils import format_log_problem, truncate_string

logger = logging.getLogger(__name__)


def next_theory_problem(progress: Progress) -> Problem:
    """Возвращает следующее теоретическое задание по текущей теме студента."""
    if progress.is_theory_completed():
        logger.error(f'( ! ) {progress.user.username:<10} [теория не завершена]'
                     f' ({truncate_string(progress.topic.title)})]')
        raise NotImplementedError('Тест по теории завершен.')
    if progress.topic.parent_topic is not None:
        if not progress.topic.parent_topic.progress_set.filter(
                user=progress.user, semester=progress.semester
        ).first().is_theory_low_reached():
            logger.error(f'( ! ) {progress.user.username:<10} [теория по предыдущей теме не завершена]'
                         f' ({truncate_string(progress.topic.parent_topic.title)})]')
            raise NotImplementedError(f'Необходимо завершить тест по теории по теме'
                                      f' {progress.topic.parent_topic}.')
    problems = filter_theory_problems(progress)
    problems = get_problems_with_max_value(progress.user, progress.semester, problems)
    last_answers = get_last_theory_user_answers(progress.user, progress.topic)
    additional_log_info = ''
    try:
        if len(last_answers) < Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_ANSWERS:
            difficulty = get_suitable_problem_difficulty(progress.skill_level)
            problems = list(filter(lambda x: x.difficulty <= difficulty, problems))
            problem = sorted(problems, key=lambda x: x.difficulty, reverse=True)[0]
            additional_log_info = (f' [калибровка ({len(last_answers)}/'
                                   f'{Constants.ALGORITHM_SKILL_LEVEL_PLACEMENT_ANSWERS})]')
        else:
            problem = problems[0]
    except IndexError:
        logger.error(f'( ! ) {progress.user.username:<10}'
                     f' [доступных теоретических заданий нет]{additional_log_info}')
        raise NotImplementedError('Доступных теоретических заданий нет.')
    logger.info(f'(   ) {format_log_problem(progress.user, problem)}{additional_log_info}')
    return problem


def next_practice_problem(user: User, semester: Semester) -> Problem:
    """Возвращает следующее практическое задание по текущей теме студента."""
    user_weakest_link_state = UserWeakestLinkState.objects.get(user=user, semester=semester).state
    if user_weakest_link_state == WeakestLinkState.IN_PROGRESS:
        weakest_link_problem = WeakestLinkProblem.objects.filter(
            user=user,
            semester=semester,
            is_solved__isnull=True
        ).order_by('group_number').first()
        logger.info(f'(   ) {format_log_problem(user, weakest_link_problem.problem)}'
                    f' [поиск проблемных тем (группа {weakest_link_problem.group_number})]')
        return weakest_link_problem.problem
    problems = filter_practice_problems(user, semester).order_by('title')
    try:
        problem = get_problems_with_max_value(user, semester, problems)[0]
    except IndexError:
        logger.error(f'( ! ) {user.username:<10} [доступных практических заданий нет]')
        raise NotImplementedError('Доступных практических заданий нет.')
    logger.info(f'(   ) {format_log_problem(user, problem)}')
    return problem
