from django.urls import path

from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import has_permission
from tasks.models import Task
from .utils import get_kpi_summary, get_kpi_target_user, resolve_kpi_date_range
from .views import productivity_heatmap_api


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reports_api(request):
    if not has_permission(request.user, "view_reports"):
        return Response({"detail": "You do not have permission to view reports."}, status=403)

    completed = Task.objects.filter(status=Task.Status.DONE).count()
    by_status = {row["status"]: row["count"] for row in Task.objects.values("status").annotate(count=Count("id"))}
    return Response({"completed_tasks": completed, "status_summary": by_status})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def kpi_api(request):
    period, start_date = resolve_kpi_date_range(request.GET.get("period", "30"))
    selected_user = get_kpi_target_user(request, request.GET.get("user"))
    summary = get_kpi_summary(selected_user, start_date=start_date)
    return Response(
        {
            "user": {
                "id": selected_user.id,
                "name": selected_user.get_full_name().strip() or selected_user.email or selected_user.username,
                "email": selected_user.email,
            },
            "period": period,
            "completion_rate": summary["completion_rate"],
            "delay_rate": summary["delay_rate"],
            "productivity_score": summary["productivity_score"],
            "total_tasks": summary["total_tasks"],
            "completed_tasks": summary["completed_tasks"],
            "delayed_tasks": summary["delayed_tasks"],
            "on_time_tasks": summary["on_time_tasks"],
            "total_work_hours": summary["total_work_hours"],
            "delay_alert": summary["delay_rate"] > 30,
        }
    )


urlpatterns = [
    path("kpi/", kpi_api, name="kpi_api"),
    path("heatmap/", productivity_heatmap_api, name="productivity_heatmap_api"),
    path("reports/", reports_api, name="reports_api"),
]
