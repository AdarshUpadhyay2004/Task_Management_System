from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.decorators import employee_required, manager_required, team_lead_required
from accounts.permissions import RoleActionPermission, get_user_role, has_permission
from gamification.models import POINTS_PER_COMPLETED_TASK, UserProfile
from .serializers import ActivityLogSerializer, TaskRiskSerializer, TaskSerializer
from .forms import TaskForm
from .models import ActivityLog, Task, TaskSession
from .priority import suggest_task_priority
from .utils import (
    calculate_progress_percentage,
    check_task_risk,
    get_task_risk_level,
    get_task_warning_message,
    get_visible_tasks_for_user,
)

User = get_user_model()


def _decorate_tasks(tasks):
    for task in tasks:
        task.risk_level = get_task_risk_level(task)
        task.progress_percentage = calculate_progress_percentage(task)
        task.warning_message = get_task_warning_message(task)
    return tasks


@login_required
def task_list(request):
    tasks = get_visible_tasks_for_user(request.user).select_related("assigned_to", "created_by").order_by("-created_at")
    active_session = None
    if has_permission(request.user, "view_assigned_tasks"):
        active_session = TaskSession.objects.filter(employee=request.user, ended_at__isnull=True).select_related("task").first()

    context = {
        "tasks": _decorate_tasks(tasks),
        "active_session": active_session,
        "role": get_user_role(request.user),
        "can_create_task": has_permission(request.user, "create_task"),
        "can_update_task": has_permission(request.user, "update_task"),
        "can_view_reports": has_permission(request.user, "view_reports"),
    }
    return render(request, "tasks/task_list.html", context)


@manager_required
def activity_log_timeline(request):
    logs = ActivityLog.objects.select_related("user", "task").order_by("-timestamp")
    task_id = request.GET.get("task")
    user_id = request.GET.get("user")
    date_value = request.GET.get("date")

    if task_id:
        logs = logs.filter(task_id=task_id)
    if user_id:
        logs = logs.filter(user_id=user_id)
    if date_value:
        logs = logs.filter(timestamp__date=date_value)

    context = {
        "logs": logs[:100],
        "selected_task": task_id or "",
        "selected_user": user_id or "",
        "selected_date": date_value or "",
        "users": User.objects.order_by("email").values_list("id", "email"),
        "tasks": Task.objects.order_by("title").values_list("id", "title"),
    }
    return render(request, "tasks/activity_log_timeline.html", context)


@team_lead_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST, current_user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.priority = suggest_task_priority(task.title, task.description)
            task.save()
            check_task_risk(task)
            messages.success(request, f"Task created with {task.get_priority_display().lower()} priority.")
            return redirect("task_list")
    else:
        form = TaskForm(current_user=request.user)
    return render(request, "tasks/admin_task_form.html", {"form": form, "mode": "create"})


@team_lead_required
def task_edit(request, task_id: int):
    task = get_object_or_404(get_visible_tasks_for_user(request.user), pk=task_id)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, current_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
            return redirect("task_list")
    else:
        form = TaskForm(instance=task, current_user=request.user)
    return render(request, "tasks/admin_task_form.html", {"form": form, "mode": "edit", "task": task})


@team_lead_required
def task_delete(request, task_id: int):
    task = get_object_or_404(get_visible_tasks_for_user(request.user), pk=task_id)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect("task_list")
    return render(request, "tasks/admin_task_delete.html", {"task": task})


@ensure_csrf_cookie
@login_required
def employee_task_list(request):
    return task_list(request)


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


@employee_required
@require_POST
def task_start(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id, assigned_to=request.user)
    if TaskSession.objects.filter(employee=request.user, ended_at__isnull=True).exists():
        msg = "Stop your current task before starting another."
        if _is_ajax(request):
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect("employee_task_list")

    TaskSession.objects.create(task=task, employee=request.user)
    if task.status != Task.Status.IN_PROGRESS:
        task.status = Task.Status.IN_PROGRESS
        task.save(update_fields=["status", "updated_at"])
    if _is_ajax(request):
        return JsonResponse({"ok": True})
    messages.success(request, "Task started.")
    return redirect("employee_task_list")


@employee_required
@require_POST
def task_stop(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id, assigned_to=request.user)
    session = TaskSession.objects.filter(task=task, employee=request.user, ended_at__isnull=True).first()
    if not session:
        msg = "No running session for this task."
        if _is_ajax(request):
            return JsonResponse({"ok": False, "error": msg}, status=400)
        messages.error(request, msg)
        return redirect("employee_task_list")

    session.stop()
    if _is_ajax(request):
        return JsonResponse({"ok": True, "duration_seconds": session.duration_seconds})
    messages.success(request, "Task stopped.")
    return redirect("employee_task_list")


@employee_required
@require_POST
def task_mark_done(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id, assigned_to=request.user)
    if TaskSession.objects.filter(task=task, employee=request.user, ended_at__isnull=True).exists():
        messages.error(request, "Stop the task before marking it done.")
        return redirect("employee_task_list")

    task.status = Task.Status.DONE
    task.completed_at = timezone.now()
    task.save(update_fields=["status", "completed_at", "updated_at"])
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    messages.success(
        request,
        (
            f"Task marked done. You earned {POINTS_PER_COMPLETED_TASK} points. "
            f"You now have {profile.points} points and are at level {profile.level}."
        ),
    )
    return redirect("employee_task_list")


class ActivityLogListAPIView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [RoleActionPermission]
    required_action = "view_reports"
    search_fields = ["action", "user__email", "task__title"]
    ordering_fields = ["timestamp", "action"]
    ordering = ["-timestamp"]

    def get_queryset(self):
        queryset = ActivityLog.objects.select_related("user", "task").all()
        user_id = self.request.query_params.get("user")
        task_id = self.request.query_params.get("task")
        date_value = self.request.query_params.get("date")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if date_value:
            queryset = queryset.filter(timestamp__date=date_value)
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        return queryset


class TaskRiskListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tasks = get_visible_tasks_for_user(request.user).select_related("assigned_to").order_by("-updated_at")

        for task in tasks:
            check_task_risk(task)

        serializer = TaskRiskSerializer(tasks, many=True)
        return Response(serializer.data)


@login_required
def task_risk_dashboard(request):
    tasks = get_visible_tasks_for_user(request.user).order_by("-updated_at")
    return render(request, "tasks/task_risk_dashboard.html", {"tasks": _decorate_tasks(tasks)})


class TaskListAPIView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_visible_tasks_for_user(self.request.user).select_related("created_by", "assigned_to").order_by("-created_at")


class TaskCreateAPIView(generics.CreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [RoleActionPermission]
    required_action = "create_task"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assigned_to = serializer.validated_data.get("assigned_to")
        if assigned_to and assigned_to.role != User.Role.EMPLOYEE:
            return Response({"assigned_to": ["Tasks can only be assigned to employees."]}, status=status.HTTP_400_BAD_REQUEST)
        if assigned_to and request.user.department and assigned_to.department != request.user.department:
            return Response({"assigned_to": ["You can only assign tasks within your department."]}, status=status.HTTP_400_BAD_REQUEST)

        task = serializer.save(created_by=request.user)
        task.priority = suggest_task_priority(task.title, task.description)
        task.save(update_fields=["priority", "updated_at"])
        check_task_risk(task)
        headers = self.get_success_headers(serializer.data)
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED, headers=headers)


# Create your views here.
