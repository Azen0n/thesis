from courses.models import Problem


def get_answer_safe_data(problem: Problem) -> dict:
    """Возвращает словарь с id и text вариантов ответа на задание
    без is_correct.
    """
    match problem.type:
        case 'Multiple Choice Radio':
            answer = {
                'type': 'Multiple Choice Radio',
                'options': [{'id': str(option.id),
                             'text': option.text} for option in
                            problem.multiplechoiceradio_set.all()]
            }
        case 'Multiple Choice Checkbox':
            answer = {
                'type': 'Multiple Choice Checkbox',
                'options': [{'id': str(option.id),
                             'text': option.text} for option in
                            problem.multiplechoicecheckbox_set.all()]
            }
        case 'Fill In Single Blank':
            answer = {
                'type': 'Fill In Single Blank',
                'problem_id': str(problem.id)
            }
        case _:
            answer = {}
    return answer
