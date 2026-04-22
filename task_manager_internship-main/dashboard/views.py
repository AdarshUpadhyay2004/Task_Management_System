from datetime import timedelta

from django.http import JsonResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import manager_required, team_lead_required
from accounts.permissions import has_permission
from django.contrib.auth import get_user_model
from tasks.models import Task, TaskSession
from .utils import (
    build_heatmap_data,
    build_kpi_leaderboard,
    build_kpi_trend,
    get_heatmap_user,
    get_kpi_summary,
    get_kpi_target_user,
    resolve_kpi_date_range,
)

User = get_user_model()

def _format_hms(total_seconds: int) -> str:
    total_seconds = int(total_seconds or 0)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@manager_required
def manager_dashboard(request):
    status_counts = {row["status"]: row["c"] for row in Task.objects.values("status").annotate(c=Count("id"))}
    employees = User.objects.filter(role=User.Role.EMPLOYEE).order_by("first_name", "last_name", "email")

    since = timezone.now().date() - timedelta(days=6)
    completed_by_day_qs = (
        Task.objects.filter(status=Task.Status.DONE, completed_at__date__gte=since)
        .annotate(day=TruncDate("completed_at"))
        .values("day")
        .annotate(c=Count("id"))
        .order_by("day")
    )
    completed_by_day = [{"day": x["day"].isoformat(), "count": x["c"]} for x in completed_by_day_qs]

    time_by_employee_qs = (
        TaskSession.objects.filter(ended_at__isnull=False)
        .values("employee__first_name", "employee__last_name", "employee__email")
        .annotate(seconds=Sum("duration_seconds"))
        .order_by("-seconds")[:10]
    )
    time_by_employee = [
        {
            "name": (f'{x["employee__first_name"]} {x["employee__last_name"]}'.strip() or x["employee__email"]),
            "seconds": int(x["seconds"] or 0),
            "hms": _format_hms(x["seconds"] or 0),
        }
        for x in time_by_employee_qs
    ]

    context = {
        "status_counts": status_counts,
        "completed_by_day": completed_by_day,
        "time_by_employee": time_by_employee,
        "employees": employees,
        "role_label": "Manager",
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@team_lead_required
def team_lead_dashboard(request):
    if request.user.department:
        team_members = User.objects.filter(department=request.user.department, role=User.Role.EMPLOYEE)
        team_tasks = Task.objects.filter(assigned_to__department=request.user.department).distinct()
    else:
        team_members = User.objects.none()
        team_tasks = Task.objects.filter(created_by=request.user)

    context = {
        "total_tasks": team_tasks.count(),
        "new_tasks": team_tasks.filter(status=Task.Status.NEW).count(),
        "in_progress_tasks": team_tasks.filter(status=Task.Status.IN_PROGRESS).count(),
        "completed_tasks": team_tasks.filter(status=Task.Status.DONE).count(),
        "team_members": team_members.order_by("first_name", "last_name", "email"),
    }
    return render(request, "dashboard/team_lead_dashboard.html", context)


@manager_required
def report_completed_tasks(request):
    tasks = Task.objects.filter(status=Task.Status.DONE).select_related("assigned_to").order_by("-completed_at")
    rows = []
    for task in tasks:
        seconds = task.total_seconds()
        rows.append({"task": task, "seconds": seconds, "hms": _format_hms(seconds)})
    return render(request, "dashboard/report_completed_tasks.html", {"rows": rows})


@manager_required
def productivity_heatmap_api(request):
    selected_user = get_heatmap_user(request, request.GET.get("user"))
    heatmap_data, tasks_by_day, ordered_days = build_heatmap_data(selected_user, days=90)

    return JsonResponse(
        {
            "user": {
                "id": selected_user.id,
                "name": selected_user.get_full_name().strip() or selected_user.email or selected_user.username,
                "email": selected_user.email,
            },
            "days": heatmap_data,
            "tasks_by_day": tasks_by_day,
            "ordered_days": ordered_days,
            "range_days": 90,
            "example_response": {
                "2026-04-01": 2.5,
                "2026-04-02": 5,
                "2026-04-03": 0,
            },
        }
    )


@manager_required
def productivity_heatmap_view(request):
    return render(
        request,
        "dashboard/productivity_heatmap.html",
        {
            "employees": User.objects.filter(role=User.Role.EMPLOYEE, is_active=True).order_by("first_name", "last_name", "email"),
            "selected_user_id": request.GET.get("user", ""),
        },
    )


@login_required
def kpi_dashboard(request):
    period, start_date = resolve_kpi_date_range(request.GET.get("period", "30"))
    selected_user = get_kpi_target_user(request, request.GET.get("user"))
    summary = get_kpi_summary(selected_user, start_date=start_date)
    trend = build_kpi_trend(selected_user, days=int(period))
    leaderboard = build_kpi_leaderboard(start_date=start_date) if has_permission(request.user, "view_reports") else []

    context = {
        "selected_user": selected_user,
        "selected_user_id": str(selected_user.id),
        "selected_period": period,
        "summary": summary,
        "trend": trend,
        "leaderboard": leaderboard,
        "employees": User.objects.filter(role=User.Role.EMPLOYEE, is_active=True).order_by("first_name", "last_name", "email"),
        "can_select_user": has_permission(request.user, "view_reports"),
        "show_delay_alert": summary["delay_rate"] > 30,
    }
    return render(request, "dashboard/kpi_dashboard.html", context)


# Create your views here.
