from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from tasks.models import Task

from .models import Notification


def notification_group_name(user_id: int) -> str:
    return f"notifications_{user_id}"


def send_notification_email(*, subject: str, message: str, recipient_list: list[str]):
    if not recipient_list:
        return
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=True,
    )


def create_notification(*, user, message: str, notification_type: str, task=None, send_email: bool = False, email_subject: str = ""):
    notification = Notification.objects.create(
        user=user,
        task=task,
        type=notification_type,
        message=message,
    )
    if send_email and user.email:
        send_notification_email(
            subject=email_subject or "Task Manager Notification",
            message=message,
            recipient_list=[user.email],
        )
    return notification


def push_notification(notification: Notification):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    unread_count = Notification.objects.filter(user=notification.user, is_read=False).count()
    async_to_sync(channel_layer.group_send)(
        notification_group_name(notification.user_id),
        {
            "type": "send.notification",
            "notification": notification.to_payload(),
            "unread_count": unread_count,
        },
    )


def process_task_deadline_notifications(*, target_date=None) -> int:
    target_date = target_date or timezone.localdate()
    tomorrow = target_date + timedelta(days=1)
    created_count = 0

    deadline_tasks = Task.objects.select_related("assigned_to").filter(
        assigned_to__isnull=False,
        due_date=tomorrow,
    ).exclude(status=Task.Status.DONE)

    for task in deadline_tasks:
        message = f"Reminder: '{task.title}' is due on {task.due_date:%Y-%m-%d}."
        exists = Notification.objects.filter(
            user=task.assigned_to,
            task=task,
            type=Notification.NotificationType.DEADLINE_NEAR,
            created_at__date=target_date,
        ).exists()
        if exists:
            continue

        create_notification(
            user=task.assigned_to,
            task=task,
            notification_type=Notification.NotificationType.DEADLINE_NEAR,
            message=message,
        )
        created_count += 1

    overdue_tasks = Task.objects.select_related("assigned_to").filter(
        assigned_to__isnull=False,
        due_date__lt=target_date,
    ).exclude(status=Task.Status.DONE)

    for task in overdue_tasks:
        message = f"Task overdue: '{task.title}' was due on {task.due_date:%Y-%m-%d}. Please update it."
        exists = Notification.objects.filter(
            user=task.assigned_to,
            task=task,
            type=Notification.NotificationType.TASK_OVERDUE,
            created_at__date=target_date,
        ).exists()
        if exists:
            continue

        create_notification(
            user=task.assigned_to,
            task=task,
            notification_type=Notification.NotificationType.TASK_OVERDUE,
            message=message,
            send_email=True,
            email_subject="Task overdue",
        )
        created_count += 1

    return created_count
