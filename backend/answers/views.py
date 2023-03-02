import json
from uuid import UUID

from django.http import HttpRequest, HttpResponse, JsonResponse

from algorithm.models import UserAnswer, Progress
from answers.create_answer import create_user_answer
from answers.utils import is_problem_main_topic_completed, validate_answer_by_type, is_parent_topic_completed
from courses.models import Semester, Problem, PRACTICE_TYPES


def validate_answer(request: HttpRequest, semester_pk: UUID, problem_pk: UUID) -> HttpResponse:
    """Проверка ответа пользователя с записью в БД и обновлением баллов."""
    semester = Semester.objects.get(id=semester_pk)
    problem = Problem.objects.get(pk=problem_pk)
    if not is_parent_topic_completed(request.user, semester, problem):
        return JsonResponse(json.dumps({'error': f'Необходимо завершить тест по теории по теме'
                                                 f' {problem.main_topic.parent_topic}.'}), safe=False)
    if problem.type in PRACTICE_TYPES:
        progress = Progress.objects.get(user=request.user, semester=semester, topic=problem.main_topic)
        if not progress.is_theory_low_reached():
            return JsonResponse(json.dumps({'error': 'Тест по теории не завершен.'}), safe=False)
    if is_problem_main_topic_completed(request.user, semester, problem):
        return JsonResponse(json.dumps({'error': 'Набран максимальный балл.'}), safe=False)
    if UserAnswer.objects.filter(problem=problem, semester=semester, user=request.user).exists():
        return JsonResponse(json.dumps({'error': 'Вы уже отправили решение по этому заданию.'}), safe=False)
    try:
        data = json.loads(request.body)
        coefficient, answer = validate_answer_by_type(data)
        create_user_answer(request.user, semester, problem, coefficient, answer)
    except (ValueError, NotImplementedError) as e:
        return JsonResponse(json.dumps({'error': str(e)}), safe=False)
    return JsonResponse(json.dumps({'coefficient': coefficient}), safe=False)
