from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack  # Add this import
from django.core.asgi import get_asgi_application
import chat.routing
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": SessionMiddlewareStack(  # Use SessionMiddlewareStack here
        AuthMiddlewareStack(  # Stack both session and auth middleware
            URLRouter(
                chat.routing.websocket_urlpatterns
            )
        )
    ),
})
