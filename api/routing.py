# api/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_identifier>[^/]+)/$", consumers.ChatConsumer.as_asgi()),
]
