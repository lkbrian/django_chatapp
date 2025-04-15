from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import api.routing  # we'll create this next

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(URLRouter(api.routing.websocket_urlpatterns)),
    }
)
