"""
HTTP cookie helpers for JWT authentication.

Centralizes cookie configuration so that views and the refresh
endpoint produce consistent Set-Cookie / Delete-Cookie headers.
"""

from django.conf import settings
from rest_framework.response import Response


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> Response:
    """
    Attach *access_token* and *refresh_token* as HttpOnly cookies.

    Args:
        response: The DRF Response to decorate.
        access_token: Encoded JWT access token.
        refresh_token: Encoded JWT refresh token.

    Returns:
        The same *response* object with Set-Cookie headers added.
    """
    secure: bool = not settings.DEBUG

    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=30 * 60,          # 30 minutes — matches ACCESS_TOKEN_LIFETIME
        httponly=True,
        secure=secure,
        samesite='Lax',
        path='/',
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=24 * 60 * 60,     # 1 day — matches REFRESH_TOKEN_LIFETIME
        httponly=True,
        secure=secure,
        samesite='Lax',
        path='/api/auth/',
    )
    return response


def clear_auth_cookies(response: Response) -> Response:
    """
    Remove JWT authentication cookies.

    Uses the same *path* values as :func:`set_auth_cookies` so the
    browser correctly matches and deletes them.

    Args:
        response: The DRF Response to decorate.

    Returns:
        The same *response* object with Delete-Cookie headers added.
    """
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/api/auth/')
    return response