import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import Notification


@login_required
@require_GET
def notification_list(request):
    notifications = list(
        Notification.objects.filter(user=request.user)
        .select_related("task")
        .values("id", "message", "type", "is_read", "created_at", "task_id")[:20]
    )
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse(
        {
            "notifications": notifications,
            "unread_count": unread_count,
        }
    )


@login_required
@require_POST
def mark_notifications_read(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}
    notification_ids = payload.get("notification_ids") or []

    queryset = Notification.objects.filter(user=request.user, is_read=False)
    if notification_ids:
        queryset = queryset.filter(id__in=notification_ids)

    updated = queryset.update(is_read=True)
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"updated": updated, "unread_count": unread_count})


@login_required
@require_POST
def mark_all_notifications_read(request):
    updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"updated": updated, "unread_count": 0})
