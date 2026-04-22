import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

from notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns
from presence.routing import websocket_urlpatterns as presence_websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(presence_websocket_urlpatterns + notification_websocket_urlpatterns)
        ),
    }
)
