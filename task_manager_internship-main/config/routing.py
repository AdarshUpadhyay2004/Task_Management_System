from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import presence.routing


application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(presence.routing.websocket_urlpatterns)
        ),
    }
)
