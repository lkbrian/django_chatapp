# Create your views here.
# from os import error
from django.contrib.auth import get_user_model
import requests
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer, UserSerializer
from .utils import (
    generate_random_titles,
    generate_username_suggestions,
    replace_existing_google_username,
)
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class check_username(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        username = request.query_params.get("username")
        if not username:
            return Response(
                {"message": "provider data"}, status=status.HTTP_400_BAD_REQUEST
            )
        User = get_user_model()

        if User.objects.filter(username=username).exists():
            suggestions = generate_username_suggestions(username)
            return Response({"available": False, "suggestions": suggestions})

        return Response({"available": True})


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")
        if not access_token:
            return Response({"error": "Access token is required"}, status=400)

        # Verify token with Google
        google_user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(
            google_user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code != 200:
            return Response({"error": "Failed to authenticate with Google"}, status=400)

        user_info = response.json()
        email = user_info.get("email")
        google_username = user_info.get("sub")
        username = replace_existing_google_username(google_username)

        if not email:
            return Response({"error": "Email not provided by Google"}, status=400)

        # Get or create user
        User = get_user_model()
        user = User.objects.filter(email=email).first()

        if not user:
            username = replace_existing_google_username(google_username)
            user = User.objects.create(
                email=email,
                username=username,
            )
            user.set_unusable_password()
            user.save()

        user_data = UserSerializer(user)
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Google login successful",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": user_data.data,
            },
            status=status.HTTP_200_OK,
        )


class CheckTitleAvailability(APIView):
    def get(self, request):
        title = request.query_params.get("title")

        if not title:
            return Response(
                {"error": "Title query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ChatRoom.objects.filter(title=title).exists():
            suggestions = generate_random_titles(base_name=title, count=5)
            return Response(
                {
                    "available": False,
                    "message": "Title already taken.",
                    "suggestions": suggestions,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"available": True, "message": "Title is available."},
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        try:
            email = data.get("email")
            password = data.get("password")
            username = data.get("username")
            if not email or not password or not username:
                return Response(
                    {"error": "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            User = get_user_model()
            if User.objects.filter(email=email).exists():
                return Response(
                    {"error": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.filter(username=username).exists():
                return Response(
                    {"error": "Username already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            User.objects.create_user(username=username, email=email, password=password)
            return Response(
                {"message": "user created successfully"}, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            error_message = str(e.orig)
            return Response(
                {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
            )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        try:
            email = data.get("email")
            password = data.get("password")
            username = data.get("username")

            if not (username or email) or not password:
                return Response({"message": "provide login cridentials"})
            User = get_user_model()
            try:
                if email:
                    user = User.objects.get(email=email)
                else:
                    user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {"message": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if user and user.check_password(password):
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                user_data = UserSerializer(user)
                return Response(
                    {
                        "message": "Login successful",
                        "access_token": access_token,
                        "refresh_token": str(refresh),
                        "user": user_data.data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "Invalid credentials"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            error_message = str(e.orig)
            return Response(
                {"error": str(error_message)}, status=status.HTTP_400_BAD_REQUEST
            )


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                error_message = str(e.orig)
                return Response(
                    {"error": f"Invalid refresh token or {error_message}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            error_message = str(e.orig)
            return Response(
                {"error": str(error_message)}, status=status.HTTP_400_BAD_REQUEST
            )


class TokenRefreshView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                token = RefreshToken(refresh_token)
                access_token = str(token.access_token)
            except Exception as e:
                error_message = str(e.orig)
                return Response(
                    {"error": f"Invalid refresh token or {error_message}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"access_token": access_token, refresh_token: str(token)},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            error_message = str(e.orig)
            return Response(
                {"error": str(error_message)}, status=status.HTTP_400_BAD_REQUEST
            )


class ChatRoomView(APIView):
    def get(self, request, pk=None):
        if pk:
            chat_room = ChatRoom.objects.filter(pk=pk).first()
            serializer = ChatRoomSerializer(chat_room)
            return Response(serializer.data)
        else:
            chat_rooms = ChatRoom.objects.all()
            serializer = ChatRoomSerializer(chat_rooms, many=True)
            return Response(serializer.data)

    def post(self, request):
        data = request.data
        try:
            title = data.get("title")
            description = data.get("description")
            created_by = request.user

            if not title or not created_by:
                return Response(
                    {"error": "Title and created_by are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not title or ChatRoom.objects.filter(title=title).exists():
                base_name = title or "chatroom"
                title = generate_random_titles(base_name, count=1)[0]
            ChatRoom.objects.create(
                title=title, description=description, created_by=created_by
            )
            return Response(
                {"message": "Chat room created successfully"},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            error_message = str(e.orig)
            return Response(
                {"error": str(error_message)}, status=status.HTTP_400_BAD_REQUEST
            )
        pass

    def patch(self, request, pk):
        data = request.data
        try:
            title = data.get("title")
            description = data.get("description")
            chat_room = ChatRoom.objects.filter(pk=pk).first()
            if not chat_room:
                return Response(
                    {"error": "Chat room not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if (
                title
                and ChatRoom.objects.filter(title=title)
                .exclude(pk=chat_room.pk)
                .exists()
            ):
                suggestions = generate_random_titles(title, count=5)
                return Response(
                    {"error": "Title already exists", "suggestions": suggestions},
                    status=status.HTTP_409_CONFLICT,
                )

            if title:
                chat_room.title = title
            if description:
                chat_room.description = description
            chat_room.save()

            return Response(
                {"message": "Chat room updated successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            error_message = str(e.orig)
            return Response(
                {"error": str(error_message)}, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, pk):
        try:
            chat_room = ChatRoom.objects.filter(pk=pk).first()
            if not chat_room:
                return Response(
                    {"error": "Chat room not found"}, status=status.HTTP_404_NOT_FOUND
                )
            chat_room.delete()
            return Response(
                {"message": "Chat room deleted successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            error_message = str(e.orig)
            return Response(
                {"error": str(error_message)}, status=status.HTTP_400_BAD_REQUEST
            )


class MessageView(APIView):
    def get(self, request):
        messages = Message.objects.all()

        # Annotate each message with is_sender status
        for message in messages:
            message.is_sender = message.user == request.user

        serializer = MessageSerializer(
            messages, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        try:
            room = data.get("room")
            content = data.get("content")
            user = request.user

            if not room or not content or not user:
                return Response(
                    {"error": "Room, content and user(all three) are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            chat_room = ChatRoom.objects.filter(pk=room).first()
            if not chat_room:
                return Response(
                    {"error": "Chat room not found"}, status=status.HTTP_404_NOT_FOUND
                )

            Message.objects.create(room=chat_room, user=user, content=content)
            return Response(
                {"message": "Message sent successfully"}, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            error_message = str(e.orig)
            return Response(
                {"error": str(error_message)}, status=status.HTTP_400_BAD_REQUEST
            )


class MessageViewWithInfiniteScroll(APIView):

    def get(self, request, pk=None):
        room_id = request.query_params.get("room")
        before = request.query_params.get("before")
        after = request.query_params.get("after")
        limit = int(request.query_params.get("limit", 100))

        if not room_id:
            return Response(
                {"error": "Room ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        chat_room = ChatRoom.objects.filter(pk=room_id).first()
        if not chat_room:
            return Response(
                {"error": "Chat room not found"}, status=status.HTTP_404_NOT_FOUND
            )

        messages = Message.objects.filter(room_id=room_id)[:limit]

        if before:
            try:
                before_time = make_aware(parse_datetime(before))
                messages = messages.filter(timestamp__lt=before_time)
            except Exception:
                return Response(
                    {"error": "Invalid 'before' timestamp"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if after:
            try:
                after_time = make_aware(parse_datetime(after))
                messages = messages.filter(timestamp__gt=after_time)
            except Exception:
                return Response(
                    {"error": "Invalid 'after' timestamp"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        for message in messages:
            message.is_sender = message.user == request.user

        serializer = MessageSerializer(
            messages, many=True, context={"request": request}
        )
        return Response(serializer.data)


class SendMessageAPIView(APIView):
    def post(self, request):
        data = request.data
        try:
            room_id = data.get("room")
            content = data.get("content")
            user = request.user

            # Validate inputs
            if not room_id or not content or not user:
                return Response(
                    {"error": "Room, content and user (all three) are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the chat room based on the room ID
            chat_room = ChatRoom.objects.filter(pk=room_id).first()
            if not chat_room:
                return Response(
                    {"error": "Chat room not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Save the message to the database
            message = Message.objects.create(room=chat_room, user=user, content=content)

            # Broadcast the saved message to WebSocket clients
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_room.room_identifier}",  # The group name based on room identifier
                {
                    "type": "chat_message",
                    "content": message.content,
                    "user": user.username,
                    "timestamp": message.timestamp.isoformat(),
                    "id": message.id,
                    "is_sender": True,  # Mark the sender's message as true
                },
            )

            # Return the message details in the response, including the timestamp and ID
            serializer = MessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            error_message = str(e)
            return Response(
                {"error": f"An error occurred: {error_message}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
