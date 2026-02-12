"""
Tests de la capa de dominio (puro Python, sin Django).
Prueban reglas de negocio, entidades, factories y excepciones.
"""

import pytest
from datetime import datetime

from users.domain.entities import User
from users.domain.factories import UserFactory
from users.domain.exceptions import (
    InvalidEmail,
    InvalidUsername,
    InvalidUserData,
    UserAlreadyInactive,
    UserNotFound
)
from users.domain.events import UserCreated, UserDeactivated, UserEmailChanged


class TestUserEntity:
    """Tests de la entidad User (reglas de negocio)."""
    
    def test_create_user_with_valid_data(self):
        """Crear un usuario con datos válidos inicia en estado activo."""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password123"
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password123"
        assert user.is_active is True
        assert user.id is None  # ID asignado al persistir
        assert isinstance(user.created_at, datetime)
    
    def test_user_validates_email_format_on_creation(self):
        """La entidad valida formato de email en __post_init__."""
        with pytest.raises(InvalidEmail):
            User(
                id=None,
                email="invalid-email",  # Sin @
                username="testuser",
                password_hash="hash",
                is_active=True,
                created_at=datetime.now()
            )
    
    def test_user_validates_empty_email(self):
        """No se permite email vacío."""
        with pytest.raises(InvalidEmail):
            User(
                id=None,
                email="",
                username="testuser",
                password_hash="hash",
                is_active=True,
                created_at=datetime.now()
            )
    
    def test_user_validates_empty_username(self):
        """No se permite username vacío."""
        with pytest.raises(InvalidUsername):
            User(
                id=None,
                email="test@example.com",
                username="",
                password_hash="hash",
                is_active=True,
                created_at=datetime.now()
            )
    
    def test_deactivate_user_changes_status_and_generates_event(self):
        """Desactivar un usuario genera evento UserDeactivated."""
        user = User(
            id="123",
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            is_active=True,
            created_at=datetime.now()
        )
        
        user.deactivate(reason="Test deactivation")
        
        assert user.is_active is False
        events = user.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], UserDeactivated)
        assert events[0].user_id == "123"
        assert events[0].reason == "Test deactivation"
    
    def test_cannot_deactivate_inactive_user(self):
        """No se puede desactivar un usuario ya inactivo."""
        user = User(
            id="123",
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            is_active=False,
            created_at=datetime.now()
        )
        
        with pytest.raises(UserAlreadyInactive) as exc_info:
            user.deactivate()
        
        assert exc_info.value.user_id == "123"
        assert "ya está inactivo" in str(exc_info.value).lower()
    
    def test_deactivate_is_idempotent_but_throws(self):
        """Intentar desactivar dos veces lanza excepción (no silencioso)."""
        user = User(
            id="123",
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            is_active=True,
            created_at=datetime.now()
        )
        
        user.deactivate()
        assert user.is_active is False
        
        # Segunda desactivación lanza excepción
        with pytest.raises(UserAlreadyInactive):
            user.deactivate()
    
    def test_change_email_updates_email_and_generates_event(self):
        """Cambiar email actualiza el campo y genera evento."""
        user = User(
            id="123",
            email="old@example.com",
            username="testuser",
            password_hash="hash",
            is_active=True,
            created_at=datetime.now()
        )
        
        user.change_email("new@example.com")
        
        assert user.email == "new@example.com"
        events = user.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], UserEmailChanged)
        assert events[0].user_id == "123"
        assert events[0].old_email == "old@example.com"
        assert events[0].new_email == "new@example.com"
    
    def test_change_email_validates_format(self):
        """Cambiar a un email inválido lanza InvalidEmail."""
        user = User(
            id="123",
            email="valid@example.com",
            username="testuser",
            password_hash="hash",
            is_active=True,
            created_at=datetime.now()
        )
        
        with pytest.raises(InvalidEmail):
            user.change_email("invalid-email")
    
    def test_change_email_is_idempotent(self):
        """Cambiar al mismo email no genera eventos (idempotente)."""
        user = User(
            id="123",
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            is_active=True,
            created_at=datetime.now()
        )
        
        user.change_email("test@example.com")  # Mismo email
        
        events = user.collect_domain_events()
        assert len(events) == 0  # No se generaron eventos
        assert user.email == "test@example.com"
    
    def test_multiple_operations_generate_multiple_events(self):
        """Múltiples operaciones generan múltiples eventos."""
        user = User(
            id="123",
            email="old@example.com",
            username="testuser",
            password_hash="hash",
            is_active=True,
            created_at=datetime.now()
        )
        
        user.change_email("new@example.com")
        user.deactivate(reason="Account closed")
        
        events = user.collect_domain_events()
        assert len(events) == 2
        assert isinstance(events[0], UserEmailChanged)
        assert isinstance(events[1], UserDeactivated)
    
    def test_collect_domain_events_clears_list(self):
        """Recolectar eventos limpia la lista interna."""
        user = User(
            id="123",
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            is_active=True,
            created_at=datetime.now()
        )
        
        user.change_email("new@example.com")
        
        # Primera recolección
        events = user.collect_domain_events()
        assert len(events) == 1
        
        # Segunda recolección está vacía
        events = user.collect_domain_events()
        assert len(events) == 0


class TestUserFactory:
    """Tests del factory para crear usuarios válidos."""
    
    def test_factory_creates_valid_user(self):
        """El factory crea un usuario válido con password hasheado."""
        user = UserFactory.create(
            email="test@example.com",
            username="testuser",
            password="mypassword123"
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash != "mypassword123"  # Debe estar hasheado
        assert len(user.password_hash) == 64  # SHA-256 hex = 64 chars
        assert user.is_active is True
    
    def test_factory_validates_email_format(self):
        """El factory valida formato de email."""
        with pytest.raises(InvalidEmail):
            UserFactory.create(
                email="invalid-email",
                username="testuser",
                password="password123"
            )
    
    def test_factory_validates_email_not_empty(self):
        """El factory no permite email vacío."""
        with pytest.raises(InvalidEmail):
            UserFactory.create(
                email="",
                username="testuser",
                password="password123"
            )
    
    def test_factory_validates_username_length(self):
        """El factory valida longitud mínima del username (3 caracteres)."""
        with pytest.raises(InvalidUsername):
            UserFactory.create(
                email="test@example.com",
                username="ab",  # Muy corto
                password="password123"
            )
    
    def test_factory_validates_username_not_empty(self):
        """El factory no permite username vacío."""
        with pytest.raises(InvalidUsername):
            UserFactory.create(
                email="test@example.com",
                username="",
                password="password123"
            )
    
    def test_factory_validates_password_length(self):
        """El factory valida longitud mínima del password (8 caracteres)."""
        with pytest.raises(InvalidUserData):
            UserFactory.create(
                email="test@example.com",
                username="testuser",
                password="short"  # Muy corto
            )
    
    def test_factory_validates_password_not_empty(self):
        """El factory no permite password vacío."""
        with pytest.raises(InvalidUserData):
            UserFactory.create(
                email="test@example.com",
                username="testuser",
                password=""
            )
    
    def test_factory_hashes_password_with_sha256(self):
        """El factory hashea el password con SHA-256."""
        user = UserFactory.create(
            email="test@example.com",
            username="testuser",
            password="mypassword123"
        )
        
        # SHA-256 de "mypassword123"
        import hashlib
        expected_hash = hashlib.sha256("mypassword123".encode()).hexdigest()
        
        assert user.password_hash == expected_hash
    
    def test_factory_creates_user_with_created_at(self):
        """El factory asigna created_at automáticamente."""
        user = UserFactory.create(
            email="test@example.com",
            username="testuser",
            password="mypassword123"
        )
        
        assert isinstance(user.created_at, datetime)
        assert user.created_at <= datetime.now()


class TestDomainEvents:
    """Tests de los eventos de dominio."""
    
    def test_user_created_event_is_frozen(self):
        """UserCreated es inmutable (frozen)."""
        event = UserCreated(
            occurred_at=datetime.now(),
            user_id="123",
            email="test@example.com",
            username="testuser"
        )
        
        with pytest.raises(Exception):  # dataclass frozen lanza FrozenInstanceError
            event.user_id = "456"
    
    def test_user_deactivated_event_is_frozen(self):
        """UserDeactivated es inmutable (frozen)."""
        event = UserDeactivated(
            occurred_at=datetime.now(),
            user_id="123",
            reason="Test"
        )
        
        with pytest.raises(Exception):
            event.reason = "New reason"
    
    def test_user_email_changed_event_is_frozen(self):
        """UserEmailChanged es inmutable (frozen)."""
        event = UserEmailChanged(
            occurred_at=datetime.now(),
            user_id="123",
            old_email="old@example.com",
            new_email="new@example.com"
        )
        
        with pytest.raises(Exception):
            event.new_email = "other@example.com"
