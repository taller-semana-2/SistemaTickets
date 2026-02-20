"""
users/serializers.py — Presentation Layer (Serialization)

Transforms data between JSON (HTTP) and Python objects.
One serializer per API operation.
Validates INPUT from the client, formats OUTPUT to the client.
Does NOT contain business logic.
"""

from rest_framework import serializers


class RegisterUserSerializer(serializers.Serializer):
    """Serializer for user registration (INPUT).

    SECURITY: No 'role' field accepted. Public registration always
    creates users with USER role. Role can only be assigned by
    an authenticated administrator.
    """

    email = serializers.EmailField(required=True)
    username = serializers.CharField(min_length=3, max_length=50, required=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login (INPUT)."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserResponseSerializer(serializers.Serializer):
    """Serializer for user representation (OUTPUT)."""

    id = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    username = serializers.CharField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)


class AuthUserSerializer(serializers.Serializer):
    """Serializer for user data in authentication responses."""

    id = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    username = serializers.CharField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()


class AuthResponseSerializer(serializers.Serializer):
    """Serializer for login/register response.

    NOTE: Tokens are no longer included in the response body.
    They are set as HttpOnly cookies by the view layer.
    """

    user = AuthUserSerializer()
