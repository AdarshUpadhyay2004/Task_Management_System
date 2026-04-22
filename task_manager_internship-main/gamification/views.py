from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import UserBadge, UserProfile, ensure_default_badges


def _profile_payload(profile: UserProfile) -> dict:
    badges = list(
        UserBadge.objects.filter(user=profile.user)
        .select_related("badge")
        .values("badge__name", "badge__description", "badge__points_required", "earned_at")
    )
    return {                                                                          
        "user": profile.user.get_full_name().strip() or profile.user.email or profile.user.username,
        "email": profile.user.email,
        "points": profile.points,
        "level": profile.level,
        "streak_count": profile.streak_count,
        "badges": [
            {
                "name": item["badge__name"],
                "description": item["badge__description"],
                "points_required": item["badge__points_required"],
                "earned_at": item["earned_at"],
            }
            for item in badges
        ],
    }


@login_required
def rewards_dashboard(request):
    ensure_default_badges()
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    leaderboard = UserProfile.objects.select_related("user").order_by("-points", "user__email")[:10]
    badges = UserBadge.objects.filter(user=request.user).select_related("badge")
    return render(
        request,
        "gamification/dashboard.html",
        {
            "profile": profile,
            "badges": badges,
            "leaderboard": leaderboard,
        },
    )


@login_required
def leaderboard_view(request):
    ensure_default_badges()
    leaderboard = UserProfile.objects.select_related("user").order_by("-points", "user__email")[:10]
    payload = [
        {
            "rank": index,
            "user": item.user.get_full_name().strip() or item.user.email or item.user.username,
            "email": item.user.email,
            "points": item.points,
            "level": item.level,
            "streak_count": item.streak_count,
        }
        for index, item in enumerate(leaderboard, start=1)
    ]
    return JsonResponse({"results": payload})


@login_required
def my_profile_view(request):
    ensure_default_badges()
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return JsonResponse(_profile_payload(profile))
