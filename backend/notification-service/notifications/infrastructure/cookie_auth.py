"""
Cookie-based JWT Stateless Authentication for consumer services.

Extends JWTStatelessUserAuthentication to read the access token from
an HttpOnly cookie first, falling back to the Authorization header.
"""

from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication


class CookieJWTStatelessAuthentication(JWTStatelessUserAuthentication):
    """
    Read JWT from the ``access_token`` HttpOnly cookie.

    Priority:
    1. ``access_token`` cookie
    2. ``Authorization: Bearer <token>`` header (fallback)

    Used in consumer services that do NOT have a local User table.
    """

    def authenticate(self, request):
        """Attempt cookie-based auth first, then fall back to header."""
        raw_token = request.COOKIES.get('access_token')
        if raw_token is not None:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        # Fallback: Authorization header
        return super().authenticate(request)
