from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "timestamp", "short_message")
    list_filter = ("timestamp", "user")
    search_fields = ("message", "response", "user__email")

    def short_message(self, obj):
        return obj.message[:60]
