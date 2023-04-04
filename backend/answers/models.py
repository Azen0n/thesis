import uuid

from django.db import models

from courses.models import Problem


class AbstractAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    explanation = models.TextField(null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class MultipleChoiceRadio(AbstractAnswer):
    """Задание на выбор одного варианта ответа (radio button)."""
    is_correct = models.BooleanField()

    def __str__(self):
        return self.text


class MultipleChoiceCheckbox(AbstractAnswer):
    """Задание на выбор нескольких вариантов ответа (checkbox)."""
    is_correct = models.BooleanField()

    def __str__(self):
        return self.text


class FillInSingleBlank(AbstractAnswer):
    """Задание на заполнение пропуска (произвольный ответ). Каждая запись
    представляет собой один из корректных вариантов ответа.
    """

    def __str__(self):
        return self.text


class Code(models.Model):
    """Практическое задание на написание кода.

    memory_limit - ограничение по памяти контейнера в байтах
    (или со специальным символом, например 100000b, 1000k, 128m, 1g).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    explanation = models.TextField(null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    timeout_seconds = models.IntegerField(default=1)
    memory_limit = models.CharField(max_length=10, default='128m')
    tests = models.TextField()

    def __str__(self):
        return (f'problem={self.problem}, timeout_seconds={self.timeout_seconds},'
                f' memory_limit={self.memory_limit}, tests={self.tests}')


class CodeAnswer(models.Model):
    """Решение пользователя задания на написание кода."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.ForeignKey(Code, on_delete=models.CASCADE)
    user_code = models.TextField()
    tests_result = models.TextField()

    def __str__(self):
        return f'tests_result={self.tests_result}, code={self.code}'


class Answer(models.Model):
    """Сущность, содержащая ответ пользователя на задание конкретного типа."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_answer = models.ForeignKey('algorithm.UserAnswer', on_delete=models.CASCADE)
    multiple_choice_radio = models.ForeignKey(MultipleChoiceRadio,
                                              on_delete=models.CASCADE,
                                              blank=True, null=True)
    multiple_choice_checkbox = models.ForeignKey(MultipleChoiceCheckbox,
                                                 on_delete=models.CASCADE,
                                                 blank=True, null=True)
    fill_in_single_blank = models.TextField(blank=True, null=True)
    code_answer = models.ForeignKey(CodeAnswer, on_delete=models.CASCADE,
                                    blank=True, null=True)

    def __str__(self):
        answer = ''
        if self.multiple_choice_radio is not None:
            answer = f'multiple_choice_radio={self.multiple_choice_radio}'
        elif self.multiple_choice_checkbox is not None:
            answer = f'multiple_choice_checkbox={self.multiple_choice_checkbox}'
        elif self.fill_in_single_blank is not None:
            answer = f'fill_in_single_blank={self.fill_in_single_blank}'
        elif self.code_answer is not None:
            answer = f'code_answer={self.code_answer}'
        return f'user_answer={self.user_answer}, {answer}'
