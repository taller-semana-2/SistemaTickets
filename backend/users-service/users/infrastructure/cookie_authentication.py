"""
Cookie-based JWT Authentication for users-service.

Extends SimpleJWT's JWTAuthentication to read the access token from
an HttpOnly cookie instead of the Authorization header.
Falls back to header-based auth for compatibility.

Uses the custom ``users.User`` model directly for DB lookups instead of
``get_user_model()`` because ``AUTH_USER_MODEL`` is not overridden in
this project (the custom model is a plain ``models.Model``, not
``AbstractUser``).
"""

from typing import Optional, Tuple

from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import Token

from users.models import User


class CookieJWTAuthentication(JWTAuthentication):
    """
    Extends JWTAuthentication to read the token from HttpOnly cookies
    and resolve the user against the custom ``users.User`` model.

    Priority:
    1. Read ``access_token`` cookie
    2. Fallback to ``Authorization: Bearer <token>`` header

    This class is ONLY used in users-service. Consumer microservices
    use ``CookieJWTStatelessAuthentication`` instead (no User table).
    """

    def authenticate(self, request: Request) -> Optional[Tuple[User, Token]]:
        """Attempt cookie-based auth first, then fall back to header."""
        raw_token: Optional[str] = request.COOKIES.get('access_token')
        if raw_token is not None:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        # Fallback: standard Authorization header
        return super().authenticate(request)

    def get_user(self, validated_token: Token) -> User:
        """
        Resolve the user from the validated JWT using ``users.User``.

        Overrides the base implementation which relies on
        ``get_user_model()`` — unsuitable here because the custom
        ``User`` model is not registered as ``AUTH_USER_MODEL``.

        Args:
            validated_token: Already-validated JWT token.

        Returns:
            The authenticated ``User`` instance.

        Raises:
            InvalidToken: If the token lacks a ``user_id`` claim.
            AuthenticationFailed: If the user does not exist or is inactive.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken("Token sin identificador de usuario")

        try:
            user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist:
            raise AuthenticationFailed(
                "Usuario no encontrado", code="user_not_found"
            )

        if not user.is_active:
            raise AuthenticationFailed(
                "Usuario inactivo", code="user_inactive"
            )

        return user
