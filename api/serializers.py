from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email"]


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = "__all__"
        read_only_fields = ["created_by", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    is_sender = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", read_only=True)
    room_identifier = serializers.CharField(
        source="room.room_identifier", read_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "content",
            "timestamp",
            "room",
            "room_identifier",
            "username",
            "is_sender",
        ]

    def get_is_sender(self, obj):
        # Get the request user from context
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.user == request.user
        return False
