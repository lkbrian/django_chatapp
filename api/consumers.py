import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.room_identifier = self.scope["url_route"]["kwargs"]["room_identifier"]
        self.room_group_name = f"chat_{self.room_identifier}"

        self.chat_room = await self.get_chat_room()
        if not self.chat_room:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")
        user = self.scope["user"]
        username = user.username if user and user.is_authenticated else "Anonymous"

        # Broadcast message to everyone in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user": username,
                "is_sender": False,  # Will be set to True for the actual sender
            },
        )

        # For the sender, send a special version with is_sender=True
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "user": username,
                    "is_sender": True,
                }
            )
        )

        if user.is_authenticated:
            await self.save_message(user, self.chat_room, message)

    async def chat_message(self, event):
        # This is received by all OTHER participants (not the sender)
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "user": event["user"],
                    "is_sender": False,  # Always False for recipients
                }
            )
        )

    @database_sync_to_async
    def get_chat_room(self):
        from .models import ChatRoom

        try:
            return ChatRoom.objects.get(room_identifier=self.room_identifier)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, user, room, content):
        from .models import Message

        return Message.objects.create(user=user, room=room, content=content)
