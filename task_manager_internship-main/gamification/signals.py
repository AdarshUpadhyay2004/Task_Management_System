from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from tasks.models import Task

from .models import UserProfile, award_points_for_completed_task


@receiver(post_save, sender="accounts.User")
def create_user_profile(sender, instance, created: bool, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(pre_save, sender=Task)
def capture_previous_task_status(sender, instance: Task, **kwargs):
    if not instance.pk:
        instance._gamification_previous_status = None
        return

    previous_status = Task.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    instance._gamification_previous_status = previous_status


@receiver(post_save, sender=Task)
def reward_completed_task(sender, instance: Task, created: bool, **kwargs):
    if created or not instance.assigned_to_id:
        return

    previous_status = getattr(instance, "_gamification_previous_status", None)
    if previous_status == Task.Status.DONE or instance.status != Task.Status.DONE:
        return

    award_points_for_completed_task(instance.assigned_to, completed_at=instance.completed_at)
