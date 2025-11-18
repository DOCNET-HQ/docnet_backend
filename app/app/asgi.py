import os
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

django_asgi_app = get_asgi_application()


def get_websocket_application():
    import chat.routing

    return URLRouter(chat.routing.websocket_urlpatterns)


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(get_websocket_application()),
    }
)
