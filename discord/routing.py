from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/discord/", consumers.ChatConsumer.as_asgi()),
]
