from django.db.models.signals import post_delete
from django.dispatch import receiver

from answers.models import Answer


@receiver(post_delete, sender=Answer)
def delete_related_code_answer(sender, instance, **kwargs):
    if instance.code_answer:
        instance.code_answer.delete()
