from django.conf import settings
from django.db import models


class Note(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-updated_at", "-created_at"]
        indexes = [
            models.Index(fields=["user", "updated_at"]),
            models.Index(fields=["user", "is_pinned"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def preview(self) -> str:
        text = (self.content or "").strip()
        if len(text) <= 140:
            return text
        return f"{text[:137]}..."
