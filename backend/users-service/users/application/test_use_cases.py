"""Tests unitarios para RegisterUserUseCase.

Verifica que el registro público SIEMPRE crea usuarios con rol USER,
independientemente de cualquier intento de escalamiento de privilegios.
"""

from unittest.mock import MagicMock

import pytest

from users.application.use_cases import RegisterUserCommand, RegisterUserUseCase
from users.domain.entities import User, UserRole
from users.domain.exceptions import UserAlreadyExists
from users.domain.factories import UserFactory


class TestRegisterUserCommand:
    """Tests para RegisterUserCommand."""

    def test_command_has_no_role_field(self) -> None:
        """SEGURIDAD: RegisterUserCommand no debe aceptar campo role."""
        command = RegisterUserCommand(
            email="test@test.com",
            username="testuser",
            password="password123",
        )

        assert not hasattr(command, "role"), "RegisterUserCommand should NOT have a 'role' field"
        assert command.email == "test@test.com"
        assert command.username == "testuser"
        assert command.password == "password123"

    def test_command_rejects_role_parameter(self) -> None:
        """SEGURIDAD: RegisterUserCommand debe rechazar role como argumento."""
        with pytest.raises(TypeError):
            RegisterUserCommand(
                email="test@test.com",
                username="testuser",
                password="password123",
                role="ADMIN",  # type: ignore[call-arg]
            )


class TestRegisterUserUseCase:
    """Tests para RegisterUserUseCase."""

    def setup_method(self) -> None:
        """Setup para cada test: crear mocks de dependencias."""
        self.mock_repository = MagicMock()
        self.mock_event_publisher = MagicMock()
        self.mock_factory = MagicMock(spec=UserFactory)

        self.use_case = RegisterUserUseCase(
            repository=self.mock_repository,
            event_publisher=self.mock_event_publisher,
            factory=self.mock_factory,
        )

    def test_execute_creates_user_with_user_role(self) -> None:
        """RegisterUserUseCase SIEMPRE crea usuarios con UserRole.USER."""
        self.mock_repository.exists_by_email.return_value = False
        mock_user = MagicMock(spec=User)
        mock_user.id = "1"
        mock_user.email = "test@test.com"
        mock_user.username = "testuser"
        mock_user.role = UserRole.USER
        self.mock_factory.create.return_value = mock_user
        self.mock_repository.save.return_value = mock_user

        command = RegisterUserCommand(
            email="test@test.com",
            username="testuser",
            password="password123",
        )

        result = self.use_case.execute(command)

        self.mock_factory.create.assert_called_once_with(
            email="test@test.com",
            username="testuser",
            password="password123",
            role=UserRole.USER,
        )
        assert result.role == UserRole.USER

    def test_execute_raises_if_email_exists(self) -> None:
        """Registro con email duplicado lanza UserAlreadyExists."""
        self.mock_repository.exists_by_email.return_value = True

        command = RegisterUserCommand(
            email="existing@test.com",
            username="testuser",
            password="password123",
        )

        with pytest.raises(UserAlreadyExists):
            self.use_case.execute(command)

    def test_execute_publishes_user_created_event(self) -> None:
        """Registro exitoso publica evento user.created."""
        self.mock_repository.exists_by_email.return_value = False
        mock_user = MagicMock(spec=User)
        mock_user.id = "1"
        mock_user.email = "test@test.com"
        mock_user.username = "testuser"
        mock_user.role = UserRole.USER
        self.mock_factory.create.return_value = mock_user
        self.mock_repository.save.return_value = mock_user

        command = RegisterUserCommand(
            email="test@test.com",
            username="testuser",
            password="password123",
        )

        self.use_case.execute(command)

        self.mock_event_publisher.publish.assert_called_once()
        call_args = self.mock_event_publisher.publish.call_args
        assert call_args[0][1] == "user.created"
