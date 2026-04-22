from django.urls import path
from . import views


urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("risk/", views.TaskRiskListAPIView.as_view(), name="task_risk_api"),
    path("risk-dashboard/", views.task_risk_dashboard, name="task_risk_dashboard"),
    path("my/", views.employee_task_list, name="employee_task_list"),
    path("create/", views.task_create, name="task_create"),
    path("<int:task_id>/edit/", views.task_edit, name="task_edit"),
    path("<int:task_id>/delete/", views.task_delete, name="task_delete"),
    path("activity-logs/", views.activity_log_timeline, name="activity_log_timeline"),
    path("<int:task_id>/start/", views.task_start, name="task_start"),
    path("<int:task_id>/stop/", views.task_stop, name="task_stop"),
    path("<int:task_id>/done/", views.task_mark_done, name="task_mark_done"),
]
