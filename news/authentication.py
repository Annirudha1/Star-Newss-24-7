from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

User = get_user_model()


TOKEN_LIFETIME = timedelta(days=7)
TOKEN_ALGORITHM = "HS256"


def generate_access_token(user):
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.pk),
        "username": user.get_username(),
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + TOKEN_LIFETIME).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=TOKEN_ALGORITHM)


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[TOKEN_ALGORITHM],
            )
        except jwt.ExpiredSignatureError as exc:
            raise exceptions.AuthenticationFailed("Token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed("Invalid token.") from exc

        user_id = payload.get("sub")
        if not user_id:
            raise exceptions.AuthenticationFailed("Invalid token payload.")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("User not found.") from exc

        if not user.is_active:
            raise exceptions.AuthenticationFailed("User account is disabled.")

        return user, token
