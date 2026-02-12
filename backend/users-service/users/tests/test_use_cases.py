"""
tests/test_use_cases.py

🎯 PROPÓSITO:
Tests de casos de uso usando mocks de repositorios y event publishers.

✅ EJEMPLO de lo que DEBE ir aquí:
    import pytest
    from unittest.mock import Mock, MagicMock
    from users.application.use_cases import CreateUserUseCase
    from users.domain.entities import User
    from users.domain.exceptions import UserAlreadyExists
    
    class TestCreateUserUseCase:
        '''Tests del caso de uso CreateUser'''
        
        def test_create_user_success(self):
            # Arrange: preparar mocks
            mock_repository = Mock()
            mock_repository.exists_by_email.return_value = False
            mock_repository.save.return_value = User(
                id='123',
                email='test@example.com',
                username='testuser',
                is_active=True
            )
            
            mock_event_publisher = Mock()
            
            use_case = CreateUserUseCase(mock_repository, mock_event_publisher)
            
            # Act: ejecutar
            result = use_case.execute(
                email='test@example.com',
                username='testuser',
                password='securepass123'
            )
            
            # Assert: verificar
            assert result.email == 'test@example.com'
            mock_repository.save.assert_called_once()
            mock_event_publisher.publish.assert_called_once()
        
        def test_create_user_with_existing_email_raises_exception(self):
            # Arrange: simular que el email ya existe
            mock_repository = Mock()
            mock_repository.exists_by_email.return_value = True
            
            mock_event_publisher = Mock()
            
            use_case = CreateUserUseCase(mock_repository, mock_event_publisher)
            
            # Act & Assert: debe lanzar excepción
            with pytest.raises(UserAlreadyExists):
                use_case.execute(
                    email='existing@example.com',
                    username='testuser',
                    password='securepass123'
                )
            
            # Verificar que NO se intentó guardar
            mock_repository.save.assert_not_called()

💡 Los tests de use cases verifican la ORQUESTACIÓN sin tocar la base de datos.
"""
