import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Notification
from .utils import notification_group_name


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.group_name = notification_group_name(user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "snapshot",
                    "unread_count": await self._get_unread_count(),
                }
            )
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "notification": event["notification"],
                    "unread_count": event["unread_count"],
                }
            )
        )

    @database_sync_to_async
    def _get_unread_count(self):
        return Notification.objects.filter(user=self.user, is_read=False).count()
