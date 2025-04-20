import os
from django.core.asgi import get_asgi_application

# Set the default Django settings module before any imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatapp.settings")

# Initialize Django ASGI application early to ensure AppRegistry is ready

# Now import Channels and routing (AFTER Django is initialized)
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import api.routing  # This should NOT import models at module level

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,  # Use the pre-loaded ASGI app
        "websocket": AuthMiddlewareStack(URLRouter(api.routing.websocket_urlpatterns)),
    }
)
