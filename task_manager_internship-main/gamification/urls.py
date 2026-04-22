from django.urls import path

from . import views


urlpatterns = [
    path("rewards/", views.rewards_dashboard, name="rewards_dashboard"),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    path("my-profile/", views.my_profile_view, name="my_profile"),
]
