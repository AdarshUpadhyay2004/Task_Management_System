from .models import Notification


def notification_summary(request):
    if not request.user.is_authenticated:
        return {
            "header_notifications": [],
            "header_unread_notifications_count": 0,
        }

    notifications = list(Notification.objects.filter(user=request.user)[:5])
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {
        "header_notifications": notifications,
        "header_unread_notifications_count": unread_count,
    }
