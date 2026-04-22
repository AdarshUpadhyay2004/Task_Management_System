import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from accounts.models import User

from .utils import serialize_user_status, update_presence


class PresenceConsumer(AsyncWebsocketConsumer):
    group_name = "online_users"

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        status_payload = await self._mark_connected()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence.status",
                "user": status_payload,
                "online_count": await self._get_online_count(),
            },
        )

    async def disconnect(self, close_code):
        user = getattr(self, "user", None)
        if user and user.is_authenticated:
            status_payload = await self._mark_disconnected()
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "presence.status",
                    "user": status_payload,
                    "online_count": await self._get_online_count(),
                },
            )

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        payload = json.loads(text_data)
        event_type = payload.get("type")

        if event_type == "heartbeat":
            status_payload = await self._touch_presence()
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "presence.status",
                    "user": status_payload,
                    "online_count": await self._get_online_count(),
                },
            )
            return

        if event_type == "typing":
            is_typing = bool(payload.get("is_typing"))
            typing_payload = await self._set_typing(is_typing)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "presence.typing",
                    "user": typing_payload,
                },
            )

    async def presence_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "status_update",
            "user": event["user"],
            "online_count": event["online_count"],
        }))

    async def presence_typing(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing_update",
            "user": event["user"],
        }))

    @database_sync_to_async
    def _mark_connected(self):
        update_presence(self.user, is_connected=True, is_typing=False, touch_last_seen=True)
        return serialize_user_status(self.user)

    @database_sync_to_async
    def _mark_disconnected(self):
        update_presence(self.user, is_connected=False, is_typing=False, touch_last_seen=True)
        return serialize_user_status(self.user)

    @database_sync_to_async
    def _touch_presence(self):
        update_presence(self.user, is_connected=True, touch_last_seen=True)
        return serialize_user_status(self.user)

    @database_sync_to_async
    def _set_typing(self, is_typing: bool):
        update_presence(self.user, is_connected=True, is_typing=is_typing, touch_last_seen=is_typing)
        return serialize_user_status(self.user)

    @database_sync_to_async
    def _get_online_count(self):
        users = User.objects.filter(is_active=True)
        return sum(1 for user in users if serialize_user_status(user)["status"] == "Online")
