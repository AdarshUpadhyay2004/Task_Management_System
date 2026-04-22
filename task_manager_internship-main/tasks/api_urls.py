from django.urls import path

from .views import ActivityLogListAPIView, TaskCreateAPIView, TaskListAPIView


urlpatterns = [
    path("tasks/", TaskListAPIView.as_view(), name="task_list_api"),
    path("tasks/create/", TaskCreateAPIView.as_view(), name="task_create_api"),
    path("logs/", ActivityLogListAPIView.as_view(), name="activity_log_list_api"),
]
