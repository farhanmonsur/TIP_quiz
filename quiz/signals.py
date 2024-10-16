from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserScore, UserQuiz
from django.utils import timezone
import logging
from django.db.models import Sum

logger = logging.getLogger(__name__)

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_score(sender, instance, created, **kwargs):
    if created:
        UserScore.objects.get_or_create(user=instance)

@receiver(post_save, sender=UserQuiz)
def set_start_time_and_full_time(sender, instance, created, **kwargs):
    if created:  # When a new UserQuiz is created
        instance.start_time = timezone.now()  
        instance.full_time = instance.quiz.question_set.aggregate(
            total_time=Sum('time'))['total_time'] or 0
        instance.save()


@receiver(post_save, sender=UserQuiz)
def update_user_score_after_quiz(sender, instance, created, **kwargs):
    user_score, created = UserScore.objects.get_or_create(user=instance.user)
    if instance.is_completed and not instance.is_score_added_total:  # Check if the quiz is completed
        user_score.update_total_score()
        instance.is_score_added_total = True

        instance.save()
        





