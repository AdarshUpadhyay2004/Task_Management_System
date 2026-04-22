from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from tasks.models import Task, TaskSession


User = get_user_model()


def get_heatmap_user(request, user_id: str | None = None):
    """
    Managers can inspect any employee by passing ?user=<id>.
    Other roles always see their own data.
    """
    if request.user.is_superuser or getattr(request.user, "role", None) == "MANAGER":
        if user_id:
            return User.objects.filter(pk=user_id, is_active=True).first() or request.user
    return request.user


def build_heatmap_data(user, days: int = 90) -> tuple[dict[str, float], dict[str, list[dict]], list[str]]:
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=days - 1)

    sessions = (
        TaskSession.objects.filter(
            employee=user,
            ended_at__isnull=False,
            started_at__date__gte=start_date,
            started_at__date__lte=end_date,
        )
        .select_related("task")
        .order_by("started_at")
    )

    totals_by_day_qs = (
        sessions.annotate(day=TruncDate("started_at"))
        .values("day")
        .annotate(total_seconds=Sum("duration_seconds"))
        .order_by("day")
    )
    totals_by_day = {
        row["day"].isoformat(): round((row["total_seconds"] or 0) / 3600, 2)
        for row in totals_by_day_qs
    }

    tasks_by_day: dict[str, list[dict]] = {}
    for session in sessions:
        day_key = timezone.localtime(session.started_at).date().isoformat()
        tasks_by_day.setdefault(day_key, [])
        tasks_by_day[day_key].append(
            {
                "task": session.task.title,
                "hours": round(session.duration_seconds / 3600, 2),
            }
        )

    heatmap_data = {}
    ordered_days = []
    current_day = start_date
    while current_day <= end_date:
        day_key = current_day.isoformat()
        heatmap_data[day_key] = totals_by_day.get(day_key, 0)
        ordered_days.append(day_key)
        current_day += timedelta(days=1)

    return heatmap_data, tasks_by_day, ordered_days


def resolve_kpi_date_range(period: str):
    period = period if period in {"7", "30"} else "30"
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=int(period) - 1)
    return period, start_date


def get_kpi_target_user(request, user_id: str | None = None):
    if request.user.is_superuser or getattr(request.user, "role", None) == User.Role.MANAGER:
        if user_id:
            return User.objects.filter(pk=user_id, is_active=True).first() or request.user
    return request.user


def get_kpi_task_queryset(user, start_date=None):
    queryset = Task.objects.filter(assigned_to=user)
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    return queryset


def get_kpi_session_queryset(user, start_date=None):
    queryset = TaskSession.objects.filter(employee=user, ended_at__isnull=False)
    if start_date:
        queryset = queryset.filter(started_at__date__gte=start_date)
    return queryset


def get_task_completion_rate(user, start_date=None) -> float:
    tasks = get_kpi_task_queryset(user, start_date=start_date)
    total_tasks = tasks.count()
    if total_tasks == 0:
        return 0.0

    completed_tasks = tasks.filter(status=Task.Status.DONE).count()
    return round((completed_tasks / total_tasks) * 100, 2)


def get_delay_rate(user, start_date=None) -> float:
    tasks = get_kpi_task_queryset(user, start_date=start_date)
    total_tasks = tasks.count()
    if total_tasks == 0:
        return 0.0

    delayed_tasks = tasks.filter(
        status=Task.Status.DONE,
        due_date__isnull=False,
        completed_at__isnull=False,
        completed_at__date__gt=F("due_date"),
    ).count()
    return round((delayed_tasks / total_tasks) * 100, 2)


def get_total_work_hours(user, start_date=None) -> float:
    total_seconds = get_kpi_session_queryset(user, start_date=start_date).aggregate(
        total=Sum("duration_seconds")
    )["total"] or 0
    return round(total_seconds / 3600, 2)


def get_productivity_score(user, start_date=None) -> float:
    tasks = get_kpi_task_queryset(user, start_date=start_date)
    completed_tasks = tasks.filter(status=Task.Status.DONE)
    completion_rate = get_task_completion_rate(user, start_date=start_date)

    total_completed = completed_tasks.count()
    if total_completed:
        on_time_completed = completed_tasks.filter(
            Q(due_date__isnull=True) | Q(completed_at__date__lte=F("due_date"))
        ).count()
        on_time_rate = round((on_time_completed / total_completed) * 100, 2)
    else:
        on_time_rate = 0.0

    total_hours = get_total_work_hours(user, start_date=start_date)
    work_hours_score = min(total_hours * 5, 100)
    score = (completion_rate * 0.5) + (on_time_rate * 0.3) + (work_hours_score * 0.2)
    return round(score, 2)


def get_kpi_summary(user, start_date=None) -> dict:
    tasks = get_kpi_task_queryset(user, start_date=start_date)
    completed_tasks = tasks.filter(status=Task.Status.DONE)
    total_tasks = tasks.count()
    completed_count = completed_tasks.count()
    delayed_count = completed_tasks.filter(
        due_date__isnull=False,
        completed_at__isnull=False,
        completed_at__date__gt=F("due_date"),
    ).count()
    total_hours = get_total_work_hours(user, start_date=start_date)

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_count,
        "delayed_tasks": delayed_count,
        "on_time_tasks": max(completed_count - delayed_count, 0),
        "total_work_hours": total_hours,
        "completion_rate": get_task_completion_rate(user, start_date=start_date),
        "delay_rate": round((delayed_count / total_tasks) * 100, 2) if total_tasks else 0.0,
        "productivity_score": get_productivity_score(user, start_date=start_date),
    }


def build_kpi_trend(user, days: int = 7) -> list[dict]:
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=days - 1)

    completions = {
        row["day"].isoformat(): row["count"]
        for row in (
            Task.objects.filter(
                assigned_to=user,
                status=Task.Status.DONE,
                completed_at__date__gte=start_date,
                completed_at__date__lte=end_date,
            )
            .annotate(day=TruncDate("completed_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
    }

    delays = {
        row["day"].isoformat(): row["count"]
        for row in (
            Task.objects.filter(
                assigned_to=user,
                status=Task.Status.DONE,
                due_date__isnull=False,
                completed_at__isnull=False,
                completed_at__date__gt=F("due_date"),
                completed_at__date__gte=start_date,
                completed_at__date__lte=end_date,
            )
            .annotate(day=TruncDate("completed_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
    }

    hours = {
        row["day"].isoformat(): round((row["seconds"] or 0) / 3600, 2)
        for row in (
            TaskSession.objects.filter(
                employee=user,
                ended_at__isnull=False,
                started_at__date__gte=start_date,
                started_at__date__lte=end_date,
            )
            .annotate(day=TruncDate("started_at"))
            .values("day")
            .annotate(seconds=Sum("duration_seconds"))
            .order_by("day")
        )
    }

    trend = []
    current_day = start_date
    while current_day <= end_date:
        key = current_day.isoformat()
        trend.append(
            {
                "day": key,
                "completed": completions.get(key, 0),
                "delayed": delays.get(key, 0),
                "hours": hours.get(key, 0),
            }
        )
        current_day += timedelta(days=1)
    return trend


def build_kpi_leaderboard(start_date=None, limit: int = 10) -> list[dict]:
    users = User.objects.filter(role=User.Role.EMPLOYEE, is_active=True).order_by("first_name", "last_name", "email")
    leaderboard = []
    for user in users:
        summary = get_kpi_summary(user, start_date=start_date)
        leaderboard.append(
            {
                "user_id": user.id,
                "name": user.get_full_name().strip() or user.email or user.username,
                "completion_rate": summary["completion_rate"],
                "delay_rate": summary["delay_rate"],
                "productivity_score": summary["productivity_score"],
                "total_work_hours": summary["total_work_hours"],
            }
        )
    return sorted(leaderboard, key=lambda row: row["productivity_score"], reverse=True)[:limit]
