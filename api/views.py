# Create your views here.
# from os import error
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .utils import generate_random_titles, generate_username_suggestions
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime


class check_username(APIView):
    def get(self, request):
        username = request.GET.get("username", "")
        User = get_user_model()

        if User.objects.filter(username=username).exists():
            suggestions = generate_username_suggestions(username)
            return Response({"available": False, "suggestions": suggestions})

        return Response({"available": True})


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

                return Response(
                    {
                        "message": "Login successful",
                        "access_token": access_token,
                        "refresh_token": str(refresh),
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
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
    def get(self, request, pk=None):
        messages = Message.objects.all()
        serializer = MessageSerializer(messages, many=True)
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

        messages = Message.objects.filter(room_id=room_id)

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

        messages = messages.order_by("-timestamp")[:limit]
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
