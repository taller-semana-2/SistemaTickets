"""
Cookie utilities for JWT authentication.

Helper functions to set and clear HttpOnly cookies for JWT tokens.
This belongs to the infrastructure layer as it deals with HTTP transport concerns.
"""

from django.conf import settings
from rest_framework.response import Response


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> Response:
    """Set JWT tokens as HttpOnly cookies on the Response.

    Args:
        response: DRF Response object to attach cookies to.
        access_token: JWT access token string.
        refresh_token: JWT refresh token string.

    Returns:
        The same Response object with cookies set.
    """
    is_production = not settings.DEBUG

    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite='Lax',
        max_age=30 * 60,  # 30 minutes (sync with ACCESS_TOKEN_LIFETIME)
        path='/',
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=is_production,
        samesite='Lax',
        max_age=24 * 60 * 60,  # 1 day (sync with REFRESH_TOKEN_LIFETIME)
        path='/api/auth/',  # Scoped to auth endpoints only
    )

    return response


def clear_auth_cookies(response: Response) -> Response:
    """Remove authentication cookies from the Response.

    Args:
        response: DRF Response object to clear cookies from.

    Returns:
        The same Response object with cookies cleared.
    """
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/api/auth/')
    return response
