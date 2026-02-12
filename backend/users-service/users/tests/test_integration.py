"""
tests/test_integration.py

🎯 PROPÓSITO:
Tests de integración que verifican el flujo completo con Django ORM y DRF.

✅ EJEMPLO de lo que DEBE ir aquí:
    import pytest
    from django.test import TestCase
    from rest_framework.test import APIClient
    from rest_framework import status
    from users.models import User as UserModel
    from users.infrastructure.repository import DjangoUserRepository
    from users.domain.entities import User
    
    @pytest.mark.django_db
    class TestUserAPI(TestCase):
        '''Tests de integración de la API de usuarios'''
        
        def setUp(self):
            self.client = APIClient()
        
        def test_create_user_via_api(self):
            '''Test: POST /api/users/ crea un usuario'''
            data = {
                'email': 'newuser@example.com',
                'username': 'newuser',
                'password': 'securepass123'
            }
            
            response = self.client.post('/api/users/', data, format='json')
            
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['email'] == 'newuser@example.com'
            
            # Verificar que se guardó en la BD
            assert UserModel.objects.filter(email='newuser@example.com').exists()
        
        def test_create_user_with_duplicate_email_returns_400(self):
            '''Test: No se puede crear usuario con email duplicado'''
            # Crear usuario existente
            UserModel.objects.create(
                email='existing@example.com',
                username='existing',
                is_active=True
            )
            
            # Intentar crear otro con el mismo email
            data = {
                'email': 'existing@example.com',
                'username': 'another',
                'password': 'securepass123'
            }
            
            response = self.client.post('/api/users/', data, format='json')
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.django_db
    class TestDjangoUserRepository(TestCase):
        '''Tests de integración del repositorio con Django ORM'''
        
        def setUp(self):
            self.repository = DjangoUserRepository()
        
        def test_save_and_find_by_id(self):
            '''Test: Guardar y recuperar un usuario'''
            user = User(
                id='123',
                email='test@example.com',
                username='testuser',
                is_active=True
            )
            
            # Guardar
            saved_user = self.repository.save(user)
            
            # Recuperar
            found_user = self.repository.find_by_id('123')
            
            assert found_user is not None
            assert found_user.email == 'test@example.com'

💡 Los tests de integración verifican que TODAS las capas funcionan juntas correctamente.
"""
