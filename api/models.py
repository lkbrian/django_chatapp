import uuid
from django.contrib.auth.models import User
from django.db import models


class ChatRoom(models.Model):
    room_identifier = models.CharField(max_length=10, unique=True, blank=True)
    title = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        User, related_name="chatrooms", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.room_identifier:
            self.room_identifier = self.generate_room_identifier()
        super().save(*args, **kwargs)

    def generate_room_identifier(self):
        while True:
            identifier = uuid.uuid4().hex[:8]
            if not ChatRoom.objects.filter(room_identifier=identifier).exists():
                return identifier

    def __str__(self):
        return self.title


class Message(models.Model):
    room = models.ForeignKey(
        ChatRoom, related_name="messages", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, related_name="messages", on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"
