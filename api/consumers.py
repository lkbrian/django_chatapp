# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from django.core.exceptions import ObjectDoesNotExist


# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         """
#         Authenticates via JWT middleware and joins the room.
#         Rejects connection if:
#         - User is not authenticated (close code 4001)
#         - Room doesn't exist (close code 4003)
#         """
#         self.room_identifier = self.scope["url_route"]["kwargs"]["room_identifier"]
#         self.room_group_name = f"chat_{self.room_identifier}"

#         # Reject unauthenticated connections
#         if not self.scope["user"].is_authenticated:
#             await self.close(code=4001)
#             return

#         # Verify room exists
#         self.chat_room = await self.get_chat_room()
#         if not self.chat_room:
#             await self.close(code=4003)
#             return

#         # Join room group
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         """Cleanly leaves the room group on disconnect"""
#         if hasattr(self, "room_group_name"):
#             await self.channel_layer.group_discard(
#                 self.room_group_name, self.channel_name
#             )

#     async def receive(self, text_data):
#         """
#         Handles incoming messages with:
#         - JSON validation
#         - Content sanitization
#         - Instant sender feedback
#         - Group broadcasting
#         """
#         try:
#             data = json.loads(text_data)
#             content = data.get("content", "").strip()

#             # Validate content
#             if not content:
#                 raise ValueError("Message cannot be empty")
#             if len(content) > 1000:
#                 raise ValueError("Message too long (max 1000 chars)")

#             user = self.scope["user"]
#             message = await self.save_message(user, self.chat_room, content)

#             # Immediate sender confirmation
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "type": "message.sent",
#                         "id": str(message.id),
#                         "content": message.content,
#                         "username": user.username,
#                         "timestamp": message.timestamp.isoformat(),
#                         "is_sender": True,
#                         "status": "delivered",
#                     }
#                 )
#             )

#             # Broadcast to other participants
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "chat.message",
#                     "id": str(message.id),
#                     "content": message.content,
#                     "username": user.username,
#                     "timestamp": message.timestamp.isoformat(),
#                     "is_sender": False,
#                 },
#             )

#         except json.JSONDecodeError:
#             await self.send(
#                 text_data=json.dumps({"type": "error", "error": "Invalid JSON format"})
#             )
#         except ValueError as e:
#             await self.send(text_data=json.dumps({"type": "error", "error": str(e)}))
#         except Exception:
#             await self.send(
#                 text_data=json.dumps(
#                     {"type": "error", "error": "Message processing failed"}
#                 )
#             )

#     async def chat_message(self, event):
#         """
#         Receives broadcast messages and sends to clients.
#         Only triggered for other participants (not sender).
#         """
#         await self.send(
#             text_data=json.dumps(
#                 {
#                     "type": "message.received",
#                     "id": event["id"],
#                     "content": event["content"],
#                     "username": event["username"],
#                     "timestamp": event["timestamp"],
#                     "is_sender": event["is_sender"],
#                 }
#             )
#         )

#     # Database operations
#     @database_sync_to_async
#     def get_chat_room(self):
#         """Retrieves chat room or returns None"""
#         from .models import ChatRoom

#         try:
#             return ChatRoom.objects.get(room_identifier=self.room_identifier)
#         except ObjectDoesNotExist:
#             return None

#     @database_sync_to_async
#     def save_message(self, user, room, content):
#         """Saves message to database"""
#         from .models import Message

#         return Message.objects.create(user=user, room=room, content=content)
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Authenticates via JWT middleware and joins the room.
        Rejects connection if:
        - User is not authenticated (close code 4001)
        - Room doesn't exist (close code 4003)
        """
        self.room_identifier = self.scope["url_route"]["kwargs"]["room_identifier"]
        self.room_group_name = f"chat_{self.room_identifier}"

        # Reject unauthenticated connections
        if not self.scope["user"].is_authenticated:
            await self.close(code=4001)
            return

        # Verify room exists
        self.chat_room = await self.get_chat_room()
        if not self.chat_room:
            await self.close(code=4003)
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Cleanly leaves the room group on disconnect"""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """
        Handles incoming messages with:
        - JSON validation
        - Content sanitization
        - Instant sender feedback
        - Group broadcasting (excluding sender)
        """
        try:
            data = json.loads(text_data)
            content = data.get("content", "").strip()

            # Validate content
            if not content:
                raise ValueError("Message cannot be empty")
            if len(content) > 1000:
                raise ValueError("Message too long (max 1000 chars)")

            user = self.scope["user"]
            message = await self.save_message(user, self.chat_room, content)

            # 1. Immediate sender confirmation (only to this client)
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "message.sent",
                        "id": str(message.id),
                        "content": message.content,
                        "username": user.username,
                        "timestamp": message.timestamp.isoformat(),
                        "is_sender": True,
                        "status": "delivered",
                    }
                )
            )

            # 2. Broadcast to others EXCLUDING sender
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "id": str(message.id),
                    "content": message.content,
                    "username": user.username,
                    "timestamp": message.timestamp.isoformat(),
                    "sender_channel": self.channel_name,  # Identify sender
                },
            )

        except json.JSONDecodeError:
            await self.send(
                text_data=json.dumps({"type": "error", "error": "Invalid JSON format"})
            )
        except ValueError as e:
            await self.send(text_data=json.dumps({"type": "error", "error": str(e)}))
        except Exception:
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "error": "Message processing failed"}
                )
            )

    async def chat_message(self, event):
        """
        Receives broadcast messages and sends to clients.
        Explicitly excludes the original sender.
        """
        if event["sender_channel"] == self.channel_name:
            return  # Skip sending to original sender

        await self.send(
            text_data=json.dumps(
                {
                    "type": "message.received",
                    "id": event["id"],
                    "content": event["content"],
                    "username": event["username"],
                    "timestamp": event["timestamp"],
                    "is_sender": False,  # Always False since sender is excluded
                }
            )
        )

    # Database operations
    @database_sync_to_async
    def get_chat_room(self):
        """Retrieves chat room or returns None"""
        from .models import ChatRoom

        try:
            return ChatRoom.objects.get(room_identifier=self.room_identifier)
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, user, room, content):
        """Saves message to database"""
        from .models import Message

        return Message.objects.create(user=user, room=room, content=content)
