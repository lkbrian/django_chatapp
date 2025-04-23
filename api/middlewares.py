from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT Auth Middleware that lazy-loads all Django dependencies
    to prevent AppRegistryNotReady errors
    """

    def __init__(self, inner):
        super().__init__(inner)
        self._cached_AnonymousUser = None
        self._cached_AccessToken = None
        self._cached_user_model = None

    async def __call__(self, scope, receive, send):
        scope["user"] = await self.get_user_from_scope(scope)
        return await super().__call__(scope, receive, send)

    async def get_user_from_scope(self, scope):
        token = self.get_token_from_scope(scope)
        if not token:
            return await self.get_anonymous_user()
        return await self.get_user_from_token(token) or await self.get_anonymous_user()

    def get_token_from_scope(self, scope):
        # Check query params first
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        if "token" in query_params:
            return query_params["token"][0]

        # Fallback to headers
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode("utf-8")
        if auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]

        return None

    @database_sync_to_async
    def get_anonymous_user(self):
        if self._cached_AnonymousUser is None:
            from django.contrib.auth.models import AnonymousUser

            self._cached_AnonymousUser = AnonymousUser()
        return self._cached_AnonymousUser

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            if self._cached_AccessToken is None:
                from rest_framework_simplejwt.tokens import AccessToken

                self._cached_AccessToken = AccessToken

            if self._cached_user_model is None:
                from django.contrib.auth import get_user_model

                self._cached_user_model = get_user_model()

            access_token = self._cached_AccessToken(token)
            return self._cached_user_model.objects.get(id=access_token["user_id"])
        except Exception:
            return None
