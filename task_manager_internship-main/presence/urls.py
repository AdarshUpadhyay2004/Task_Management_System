from django.urls import path

from . import views


urlpatterns = [
    path("users/status/", views.user_status_api, name="user_status_api"),
    path("team/presence/", views.team_presence_view, name="team_presence"),
]
