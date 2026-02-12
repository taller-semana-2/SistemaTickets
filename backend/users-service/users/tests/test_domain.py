"""
tests/test_domain.py

🎯 PROPÓSITO:
Tests unitarios de la capa de dominio (100% aislados, sin Django).

✅ EJEMPLO de lo que DEBE ir aquí:
    import pytest
    from users.domain.entities import User
    from users.domain.factories import UserFactory
    from users.domain.exceptions import (
        InvalidEmail,
        InvalidUsername,
        UserAlreadyInactive
    )
    
    class TestUserEntity:
        '''Tests de la entidad User'''
        
        def test_user_creation_valid(self):
            user = User(
                id='123',
                email='test@example.com',
                username='testuser',
                is_active=True
            )
            assert user.email == 'test@example.com'
            assert user.is_active is True
        
        def test_deactivate_user(self):
            user = User('123', 'test@example.com', 'testuser', is_active=True)
            user.deactivate()
            assert user.is_active is False
        
        def test_deactivate_already_inactive_user_raises_exception(self):
            user = User('123', 'test@example.com', 'testuser', is_active=False)
            with pytest.raises(UserAlreadyInactive):
                user.deactivate()
    
    class TestUserFactory:
        '''Tests de la factory'''
        
        def test_create_valid_user(self):
            user = UserFactory.create(
                email='test@example.com',
                username='testuser',
                password='securepassword123'
            )
            assert user.email == 'test@example.com'
            assert user.is_active is True
        
        def test_create_with_invalid_email_raises_exception(self):
            with pytest.raises(InvalidEmail):
                UserFactory.create(
                    email='invalid-email',
                    username='testuser',
                    password='securepassword123'
                )
        
        def test_create_with_short_username_raises_exception(self):
            with pytest.raises(InvalidUsername):
                UserFactory.create(
                    email='test@example.com',
                    username='ab',  # Muy corto
                    password='securepassword123'
                )

💡 Los tests de dominio son RÁPIDOS porque no dependen de base de datos ni frameworks.
"""
