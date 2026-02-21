"""
Authentication adapter for users-service.
Uses users.User (UUID PK) when validating JWTs.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings

from users.models import User


class UsersServiceJWTAuthentication(JWTAuthentication):
    """JWT auth that resolves users against users.User (UUID primary key)."""

    def get_user(self, validated_token):
        """Return authenticated user or raise an auth error in Spanish."""
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError as exc:
            raise InvalidToken("Token sin user_id") from exc

        try:
            user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("Usuario no encontrado", code="user_not_found") from exc

        if not user.is_active:
            raise AuthenticationFailed("Usuario inactivo", code="user_inactive")

        return user
