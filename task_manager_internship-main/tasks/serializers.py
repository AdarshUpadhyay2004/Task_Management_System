from rest_framework import serializers

from .models import ActivityLog, Task
from .utils import calculate_progress_percentage, get_task_risk_level, get_task_warning_message


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "user",
            "user_email",
            "task",
            "task_title",
            "action",
            "old_value",
            "new_value",
            "timestamp",
        ]


class TaskRiskSerializer(serializers.ModelSerializer):
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True)
    risk_level = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    warning_message = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "status",
            "due_date",
            "estimated_hours",
            "predicted_delay",
            "assigned_to_email",
            "risk_level",
            "progress_percentage",
            "warning_message",
        ]

    def get_risk_level(self, obj):
        return get_task_risk_level(obj)

    def get_progress_percentage(self, obj):
        return calculate_progress_percentage(obj)

    def get_warning_message(self, obj):
        return get_task_warning_message(obj)


class TaskSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "estimated_hours",
            "predicted_delay",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_email",
            "assigned_to",
            "assigned_to_email",
        ]
        read_only_fields = ["created_by", "created_by_email", "priority", "created_at", "updated_at"]
