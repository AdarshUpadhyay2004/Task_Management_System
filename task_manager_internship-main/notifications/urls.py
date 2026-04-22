from django.urls import path

from . import views


urlpatterns = [
    path("", views.notification_list, name="notification_list"),
    path("read/", views.mark_notifications_read, name="notification_mark_read"),
    path("read-all/", views.mark_all_notifications_read, name="notification_mark_all_read"),
]
