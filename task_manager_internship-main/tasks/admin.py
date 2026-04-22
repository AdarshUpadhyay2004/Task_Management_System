from django.contrib import admin

from .models import ActivityLog, Task, TaskSession


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "priority", "status", "assigned_to", "created_by", "created_at", "completed_at")
    list_filter = ("priority", "status",)
    search_fields = ("title", "description", "assigned_to__email")


@admin.register(TaskSession)
class TaskSessionAdmin(admin.ModelAdmin):
    list_display = ("task", "employee", "started_at", "ended_at", "duration_seconds")
    list_filter = ("ended_at",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "task", "action")
    list_filter = ("user", "timestamp", "action")
    search_fields = ("action", "user__email", "task__title")
    date_hierarchy = "timestamp"
    readonly_fields = ("user", "task", "action", "old_value", "new_value", "timestamp")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "task")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# Register your models here.
