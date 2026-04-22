from django.contrib import admin

from .models import Badge, UserBadge, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "level", "streak_count", "last_completed_date")
    search_fields = ("user__email", "user__username", "user__first_name", "user__last_name")
    list_filter = ("level", "streak_count")


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "points_required")
    search_fields = ("name",)
    ordering = ("points_required",)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "earned_at")
    search_fields = ("user__email", "badge__name")
    list_filter = ("badge",)
