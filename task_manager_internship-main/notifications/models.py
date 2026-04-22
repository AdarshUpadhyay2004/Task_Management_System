from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        TASK_ASSIGNED = "TASK_ASSIGNED", "Task assigned"
        DEADLINE_NEAR = "DEADLINE_NEAR", "Deadline near"
        TASK_OVERDUE = "TASK_OVERDUE", "Task overdue"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
            models.Index(fields=["type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_type_display()}"

    def to_payload(self):
        return {
            "id": self.id,
            "message": self.message,
            "type": self.type,
            "type_display": self.get_type_display(),
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "task_id": self.task_id,
        }
