from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from .utils import serialize_user_status


User = get_user_model()


@login_required
def user_status_api(request):
    users = User.objects.filter(is_active=True).order_by("first_name", "last_name", "email")
    results = [serialize_user_status(user) for user in users]
    online_count = sum(1 for item in results if item["status"] == "Online")
    return JsonResponse({"online_count": online_count, "results": results})


@login_required
def team_presence_view(request):
    users = User.objects.filter(is_active=True).order_by("first_name", "last_name", "email")
    user_statuses = [serialize_user_status(user) for user in users]
    online_count = sum(1 for item in user_statuses if item["status"] == "Online")
    return render(
        request,
        "presence/team_presence.html",
        {
            "user_statuses": user_statuses,
            "online_count": online_count,
            "user_status_api": reverse("user_status_api"),
        },
    )
