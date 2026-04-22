from __future__ import annotations

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .middleware import get_current_user
from .models import ActivityLog, Task, TaskSession
from .utils import check_task_risk


TRACKED_FIELDS = (
    "title",
    "description",
    "status",
    "priority",
    "assigned_to_id",
    "completed_at",
    "due_date",
    "estimated_hours",
    "predicted_delay",
)


def _get_actor(task: Task | None = None):
    user = get_current_user()
    if user and getattr(user, "is_authenticated", False):
        return user
    if task and task.created_by_id:
        return task.created_by
    return None


def _display_user(user):
    if not user:
        return "System"
    full_name = user.get_full_name().strip()
    return full_name or user.email or user.username


def _task_snapshot(task: Task) -> dict:
    return {
        "title": task.title,
        "description": task.description,
        "status": task.get_status_display(),
        "priority": task.get_priority_display(),
        "assigned_to": task.assigned_to.email if task.assigned_to else None,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "estimated_hours": task.estimated_hours,
        "predicted_delay": task.predicted_delay,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


def _create_log(*, user, task, action: str, old_value: dict | None = None, new_value: dict | None = None):
    if not user:
        return
    ActivityLog.objects.create(
        user=user,
        task=task,
        action=action,
        old_value=ActivityLog.serialize_payload(old_value),
        new_value=ActivityLog.serialize_payload(new_value),
    )


@receiver(pre_save, sender=Task)
def capture_task_before_update(sender, instance: Task, **kwargs):
    if not instance.pk:
        instance._activity_previous_state = None
        return

    previous = (
        Task.objects.select_related("assigned_to", "created_by")
        .filter(pk=instance.pk)
        .first()
    )
    instance._activity_previous_state = previous


@receiver(post_save, sender=Task)
def log_task_activity(sender, instance: Task, created: bool, **kwargs):
    check_task_risk(instance)
    actor = _get_actor(instance)
    if not actor:
        return

    if created:
        _create_log(
            user=actor,
            task=instance,
            action=f"{_display_user(actor)} created task '{instance.title}'",
            new_value=_task_snapshot(instance),
        )
        return

    previous = getattr(instance, "_activity_previous_state", None)
    if not previous:
        return

    changes = {}
    for field in TRACKED_FIELDS:
        old_value = getattr(previous, field)
        new_value = getattr(instance, field)
        if old_value != new_value:
            changes[field] = {"old": old_value, "new": new_value}

    if not changes:
        return

    if "status" in changes:
        _create_log(
            user=actor,
            task=instance,
            action=(
                f"{_display_user(actor)} changed status from "
                f"{previous.get_status_display()} to {instance.get_status_display()}"
            ),
            old_value={"status": previous.get_status_display()},
            new_value={"status": instance.get_status_display()},
        )

    if "assigned_to_id" in changes:
        _create_log(
            user=actor,
            task=instance,
            action=(
                f"{_display_user(actor)} reassigned task from "
                f"{previous.assigned_to.email if previous.assigned_to else 'Unassigned'} to "
                f"{instance.assigned_to.email if instance.assigned_to else 'Unassigned'}"
            ),
            old_value={"assigned_to": previous.assigned_to.email if previous.assigned_to else None},
            new_value={"assigned_to": instance.assigned_to.email if instance.assigned_to else None},
        )

    generic_changes = {}
    for field_name in ("title", "description", "priority", "completed_at", "due_date", "estimated_hours", "predicted_delay"):
        if field_name in changes:
            generic_changes[field_name] = {
                "old": changes[field_name]["old"].isoformat() if field_name in {"completed_at", "due_date"} and changes[field_name]["old"] else changes[field_name]["old"],
                "new": changes[field_name]["new"].isoformat() if field_name in {"completed_at", "due_date"} and changes[field_name]["new"] else changes[field_name]["new"],
            }

    if generic_changes:
        changed_fields = ", ".join(generic_changes.keys())
        _create_log(
            user=actor,
            task=instance,
            action=f"{_display_user(actor)} updated task fields: {changed_fields}",
            old_value={key: value["old"] for key, value in generic_changes.items()},
            new_value={key: value["new"] for key, value in generic_changes.items()},
        )


@receiver(post_delete, sender=Task)
def log_task_deletion(sender, instance: Task, **kwargs):
    actor = _get_actor(instance)
    if not actor:
        return

    _create_log(
        user=actor,
        task=None,
        action=f"{_display_user(actor)} deleted task '{instance.title}'",
        old_value=_task_snapshot(instance),
    )


@receiver(post_save, sender=TaskSession)
def update_task_risk_on_session_save(sender, instance: TaskSession, **kwargs):
    check_task_risk(instance.task)


@receiver(post_delete, sender=TaskSession)
def update_task_risk_on_session_delete(sender, instance: TaskSession, **kwargs):
    check_task_risk(instance.task)
