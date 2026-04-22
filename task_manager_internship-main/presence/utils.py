from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from .models import UserProfile


STATUS_ONLINE = "Online"
STATUS_IDLE = "Idle"
STATUS_OFFLINE = "Offline"


def get_or_create_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def update_presence(user, *, is_connected=None, is_typing=None, touch_last_seen=True) -> UserProfile:
    profile = get_or_create_profile(user)

    if touch_last_seen:
        profile.last_seen = timezone.now()
    if is_connected is not None:
        profile.is_connected = is_connected
    if is_typing is not None:
        profile.is_typing = is_typing

    profile.save(update_fields=["last_seen", "is_connected", "is_typing"])
    return profile


def get_user_status(user) -> str:
    profile = get_or_create_profile(user)
    now = timezone.now()

    if not profile.is_connected:
        return STATUS_OFFLINE

    if profile.last_seen >= now - timedelta(minutes=1):
        return STATUS_ONLINE

    if profile.last_seen >= now - timedelta(minutes=5):
        return STATUS_IDLE

    return STATUS_OFFLINE


def get_last_seen_text(user) -> str:
    profile = get_or_create_profile(user)
    if not profile.last_seen:
        return "Never seen"

    delta = timezone.now() - profile.last_seen
    minutes = int(delta.total_seconds() // 60)

    if minutes <= 0:
        return "Last seen just now"
    if minutes == 1:
        return "Last seen 1 minute ago"
    return f"Last seen {minutes} minutes ago"


def serialize_user_status(user) -> dict:
    profile = get_or_create_profile(user)
    return {
        "id": user.id,
        "name": user.get_full_name().strip() or user.email or user.username,
        "email": user.email,
        "status": get_user_status(user),
        "last_seen": profile.last_seen.isoformat() if profile.last_seen else None,
        "last_seen_text": get_last_seen_text(user),
        "is_typing": profile.is_typing,
    }
