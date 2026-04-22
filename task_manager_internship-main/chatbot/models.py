from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp", "id"]

    def __str__(self) -> str:
        return f"{self.user} - {self.timestamp:%Y-%m-%d %H:%M}"
