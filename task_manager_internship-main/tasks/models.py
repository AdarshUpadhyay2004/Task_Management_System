import json

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Task(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        DONE = "DONE", "Done"

    class Priority(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_tasks")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(null=True, blank=True)
    predicted_delay = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def total_seconds(self) -> int:
        agg = self.sessions.aggregate(total=Sum("duration_seconds"))["total"]
        return int(agg or 0)

    def total_hours(self) -> float:
        return round(self.total_seconds() / 3600, 2)

    def __str__(self) -> str:
        return self.title


class TaskSession(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="sessions")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_sessions")
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["employee", "ended_at"]),
            models.Index(fields=["task", "employee", "ended_at"]),
        ]

    def stop(self):
        if self.ended_at:
            return
        self.ended_at = timezone.now()
        self.duration_seconds = max(0, int((self.ended_at - self.started_at).total_seconds()))
        self.save(update_fields=["ended_at", "duration_seconds"])

    def __str__(self) -> str:
        return f"{self.employee_id} {self.task_id} {self.started_at}"


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=255)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["task", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]

    @staticmethod
    def serialize_payload(payload: dict | None) -> str:
        if not payload:
            return ""
        return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)

    def __str__(self) -> str:
        return self.action


# Create your models here.
