from datetime import timedelta

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from tasks.models import Task

from .models import Notification
from .utils import create_notification, push_notification


@receiver(pre_save, sender=Task)
def capture_previous_assignee(sender, instance: Task, **kwargs):
    if not instance.pk:
        instance._previous_assigned_to_id = None
        return

    previous = Task.objects.filter(pk=instance.pk).values("assigned_to_id").first()
    instance._previous_assigned_to_id = previous["assigned_to_id"] if previous else None


@receiver(post_save, sender=Task)
def create_task_assignment_notification(sender, instance: Task, created: bool, **kwargs):
    if not instance.assigned_to:
        return

    previous_assigned_to_id = getattr(instance, "_previous_assigned_to_id", None)
    assignment_changed = created or previous_assigned_to_id != instance.assigned_to_id
    if not assignment_changed:
        return

    message = f"You have been assigned a new task: '{instance.title}'."
    create_notification(
        user=instance.assigned_to,
        task=instance,
        notification_type=Notification.NotificationType.TASK_ASSIGNED,
        message=message,
        send_email=True,
        email_subject="New task assigned",
    )


@receiver(post_save, sender=Task)
def create_due_date_notifications_on_save(sender, instance: Task, **kwargs):
    if not instance.assigned_to or not instance.due_date or instance.status == Task.Status.DONE:
        return

    today = timezone.localdate()
    if instance.due_date == today + timedelta(days=1):
        exists = Notification.objects.filter(
            user=instance.assigned_to,
            task=instance,
            type=Notification.NotificationType.DEADLINE_NEAR,
            created_at__date=today,
        ).exists()
        if not exists:
            create_notification(
                user=instance.assigned_to,
                task=instance,
                notification_type=Notification.NotificationType.DEADLINE_NEAR,
                message=f"Reminder: '{instance.title}' is due on {instance.due_date:%Y-%m-%d}.",
            )

    if instance.due_date < today:
        exists = Notification.objects.filter(
            user=instance.assigned_to,
            task=instance,
            type=Notification.NotificationType.TASK_OVERDUE,
            created_at__date=today,
        ).exists()
        if not exists:
            create_notification(
                user=instance.assigned_to,
                task=instance,
                notification_type=Notification.NotificationType.TASK_OVERDUE,
                message=f"Task overdue: '{instance.title}' was due on {instance.due_date:%Y-%m-%d}. Please update it.",
                send_email=True,
                email_subject="Task overdue",
            )


@receiver(post_save, sender=Notification)
def push_notification_realtime(sender, instance: Notification, created: bool, **kwargs):
    if created:
        push_notification(instance)
