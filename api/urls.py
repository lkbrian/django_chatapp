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
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("check_username/", check_username.as_view(), name="check_username"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("chatroom/", ChatRoomView.as_view(), name="chatroom"),
    path("check_title/", CheckTitleAvailability.as_view(), name="check_title"),
    path("message/", MessageView.as_view(), name="message"),
    path(
        "messages/infinite/",
        MessageViewWithInfiniteScroll.as_view(),
        name="message_scroll",
    ),
]
