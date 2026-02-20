"""
Cookie-based JWT Authentication for users-service.

Extends SimpleJWT's JWTAuthentication to read the access token from
an HttpOnly cookie instead of the Authorization header.
Falls back to header-based auth for compatibility.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Extends JWTAuthentication to read the token from HttpOnly cookies.

    Priority:
    1. Read ``access_token`` cookie
    2. Fallback to ``Authorization: Bearer <token>`` header

    This class is ONLY used in users-service. Other microservices
    continue using ``JWTStatelessUserAuthentication`` with the Bearer header.
    """

    def authenticate(self, request):
        """Attempt cookie-based auth first, then fall back to header."""
        raw_token = request.COOKIES.get('access_token')
        if raw_token is not None:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        # Fallback: Authorization header (for compatibility)
        return super().authenticate(request)
