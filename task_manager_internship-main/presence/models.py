from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="presence_profile",
    )
    last_seen = models.DateTimeField(default=timezone.now)
    is_connected = models.BooleanField(default=False)
    is_typing = models.BooleanField(default=False)

    class Meta:
        ordering = ["user__first_name", "user__last_name", "user__email"]

    def __str__(self) -> str:
        return f"{self.user.email} presence"
