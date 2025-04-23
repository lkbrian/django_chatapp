from django.urls import path

from .views import (
    ChatRoomView,
    CheckTitleAvailability,
    MessageView,
    MessageViewWithInfiniteScroll,
    RegisterView,
    LoginView,
    TokenRefreshView,
    check_username,
    LogoutView,
)


urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/login/google/", LoginView.as_view(), name="login"),
    path("auth/check_username/", check_username.as_view(), name="check_username"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("chat/chatroom/", ChatRoomView.as_view(), name="chatroom"),
    path("chat/check_title/", CheckTitleAvailability.as_view(), name="check_title"),
    path("chat/message", MessageView.as_view(), name="message"),
    path(
        "chat/messages/infinite/",
        MessageViewWithInfiniteScroll.as_view(),
        name="message_scroll",
    ),
]
