from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


POINTS_PER_COMPLETED_TASK = 10
POINTS_PER_LEVEL = 100
DEFAULT_BADGES = (
    ("Beginner", "Awarded for reaching 50 points.", 50),
    ("Pro", "Awarded for reaching 200 points.", 200),
    ("Expert", "Awarded for reaching 500 points.", 500),
)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak_count = models.IntegerField(default=0)
    last_completed_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-points", "user__email"]

    def __str__(self) -> str:
        return f"{self.user.email} profile"

    @staticmethod
    def calculate_level(points: int) -> int:
        return max(1, (points // POINTS_PER_LEVEL) + 1)

    def update_streak(self, completed_date):
        if not completed_date:
            return

        if self.last_completed_date == completed_date:
            return

        if self.last_completed_date == completed_date - timedelta(days=1):
            self.streak_count += 1
        else:
            self.streak_count = 1

        self.last_completed_date = completed_date

    def add_points(self, points: int, completed_date=None):
        self.points += points
        self.level = self.calculate_level(self.points)
        if completed_date:
            self.update_streak(completed_date)


class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    points_required = models.IntegerField()

    class Meta:
        ordering = ["points_required", "name"]

    def __str__(self) -> str:
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_badges",
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="user_badges",
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-earned_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="unique_user_badge"),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.badge.name}"


def ensure_default_badges():
    for name, description, points_required in DEFAULT_BADGES:
        Badge.objects.get_or_create(
            name=name,
            defaults={
                "description": description,
                "points_required": points_required,
            },
        )


def award_points_for_completed_task(user, completed_at=None):
    completed_date = timezone.localdate(completed_at or timezone.now())
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.add_points(POINTS_PER_COMPLETED_TASK, completed_date=completed_date)
    profile.save(update_fields=["points", "level", "streak_count", "last_completed_date"])

    ensure_default_badges()
    earned_badge_ids = set(
        UserBadge.objects.filter(user=user).values_list("badge_id", flat=True)
    )
    available_badges = Badge.objects.filter(points_required__lte=profile.points)

    new_user_badges = [
        UserBadge(user=user, badge=badge)
        for badge in available_badges
        if badge.id not in earned_badge_ids
    ]
    if new_user_badges:
        UserBadge.objects.bulk_create(new_user_badges)

    return profile
