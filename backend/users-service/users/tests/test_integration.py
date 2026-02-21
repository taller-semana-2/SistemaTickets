"""Tests de integración para el endpoint de registro de usuarios.

Verifica que el endpoint POST /api/auth/ NO permite escalamiento de privilegios.
"""

import pytest
import uuid
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from users.domain.entities import UserRole
from users.domain.factories import UserFactory
from users.infrastructure.event_publisher import RabbitMQEventPublisher
from users.infrastructure.repository import DjangoUserRepository


@pytest.mark.django_db
class TestRegistrationEndpoint:
    """Tests de integración para POST /api/auth/."""

    def setup_method(self) -> None:
        self.publish_patcher = patch.object(RabbitMQEventPublisher, "publish", return_value=None)
        self.publish_patcher.start()
        self.client = APIClient()

    def teardown_method(self) -> None:
        self.publish_patcher.stop()

    def test_register_ignores_role_admin(self) -> None:
        """SEGURIDAD: Enviar role=ADMIN en registro crea usuario con role USER."""
        response = self.client.post(
            "/api/auth/",
            {
                "email": "attacker@test.com",
                "username": "attacker",
                "password": "password123",
                "role": "ADMIN",  # Attempted privilege escalation
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == "USER"

    def test_register_without_role_creates_user(self) -> None:
        """Registro normal sin role crea usuario con role USER."""
        response = self.client.post(
            "/api/auth/",
            {
                "email": "normal@test.com",
                "username": "normaluser",
                "password": "password123",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == "USER"

    def test_register_duplicate_email_fails(self) -> None:
        """Registro con email duplicado retorna 400 (no regresión)."""
        self.client.post(
            "/api/auth/",
            {
                "email": "dup@test.com",
                "username": "user1",
                "password": "password123",
            },
            format="json",
        )

        response = self.client.post(
            "/api/auth/",
            {
                "email": "dup@test.com",
                "username": "user2",
                "password": "password123",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password_fails(self) -> None:
        """Registro con password corto retorna 400 (no regresión)."""
        response = self.client.post(
            "/api/auth/",
            {
                "email": "short@test.com",
                "username": "shortpwd",
                "password": "abc",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_by_role_admin_returns_users(self) -> None:
        """GET /api/auth/by-role/ADMIN/ retorna lista de admins con JWT válido."""
        repository = DjangoUserRepository()
        factory = UserFactory()
        unique_suffix = uuid.uuid4().hex
        admin_user = factory.create(
            email=f"admin_{unique_suffix}@test.com",
            username=f"admin_{unique_suffix}",
            password="password123",
            role=UserRole.ADMIN,
        )
        repository.save(admin_user)

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "email": admin_user.email,
                "password": "password123",
            },
            format="json",
        )

        assert login_response.status_code == status.HTTP_200_OK
        access_token = login_response.data["tokens"]["access"]

        response = self.client.get(
            "/api/auth/by-role/ADMIN/",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        assert response.status_code == status.HTTP_200_OK
        assert any(
            user["email"] == admin_user.email and user["role"] == "ADMIN"
            for user in response.data
        )
