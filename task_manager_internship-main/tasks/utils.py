from __future__ import annotations

from django.db.models import Sum
from django.db.models import Q
from django.utils import timezone

from .models import Task


RISK_ON_TRACK = "On Track"
RISK_AT_RISK = "At Risk"
RISK_HIGH_RISK = "High Risk"
RISK_DELAYED = "Delayed"


def calculate_progress_percentage(task: Task) -> float:
    if not task.estimated_hours or task.estimated_hours <= 0:
        return 0.0

    total_seconds = (
        task.sessions.aggregate(total=Sum("duration_seconds"))["total"]
        or 0
    )
    spent_hours = total_seconds / 3600
    progress = (spent_hours / task.estimated_hours) * 100
    return round(min(progress, 100), 2)


def get_task_risk_level(task: Task) -> str:
    if task.status == Task.Status.DONE:
        return RISK_ON_TRACK

    today = timezone.localdate()
    progress_percentage = calculate_progress_percentage(task)

    if task.due_date and task.due_date < today:
        return RISK_DELAYED

    if task.due_date and (task.due_date - today).days <= 1:
        return RISK_HIGH_RISK

    if task.estimated_hours and progress_percentage >= 80:
        return RISK_AT_RISK

    return RISK_ON_TRACK


def check_task_risk(task: Task) -> str:
    """
    Update predicted_delay for the task and return the current risk level.
    """
    risk_level = get_task_risk_level(task)
    predicted_delay = risk_level in {RISK_AT_RISK, RISK_HIGH_RISK, RISK_DELAYED}

    if task.predicted_delay != predicted_delay:
        Task.objects.filter(pk=task.pk).update(predicted_delay=predicted_delay)
        task.predicted_delay = predicted_delay

    return risk_level


def get_task_warning_message(task: Task) -> str:
    risk_level = get_task_risk_level(task)
    if risk_level == RISK_ON_TRACK:
        return ""
    return "This task may be delayed based on current progress."


def get_visible_tasks_for_user(user):
    if not getattr(user, "is_authenticated", False):
        return Task.objects.none()

    if getattr(user, "is_superuser", False) or getattr(user, "role", None) == "MANAGER":
        return Task.objects.all()

    if getattr(user, "role", None) == "TEAM_LEAD":
        filters = Q(created_by=user) | Q(assigned_to=user)
        if getattr(user, "department", ""):
            filters |= Q(created_by__department=user.department) | Q(assigned_to__department=user.department)
        return Task.objects.filter(filters).distinct()

    return Task.objects.filter(assigned_to=user)
