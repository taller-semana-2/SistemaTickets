"""
users/views.py

📋 CAPA DE PRESENTACIÓN - Controladores HTTP

🎯 PROPÓSITO:
Thin controllers que delegan TODA la lógica a los casos de uso.

📐 ESTRUCTURA:
- ViewSets de DRF para operaciones CRUD
- Cada acción ejecuta UN caso de uso
- Captura excepciones de dominio y las convierte en respuestas HTTP
- NO contiene lógica de negocio

✅ EJEMPLO de lo que DEBE ir aquí:
    from rest_framework import viewsets, status
    from rest_framework.decorators import action
    from rest_framework.response import Response
    
    from users.application.use_cases import (
        CreateUserUseCase,
        GetUserUseCase,
        DeactivateUserUseCase
    )
    from users.infrastructure.repository import DjangoUserRepository
    from users.infrastructure.event_publisher import RabbitMQEventPublisher
    from users.serializers import (
        CreateUserSerializer,
        UserSerializer,
        DeactivateUserSerializer
    )
    from users.domain.exceptions import (
        UserAlreadyExists,
        InvalidEmail,
        UserNotFound
    )
    
    class UserViewSet(viewsets.ViewSet):
        '''ViewSet para gestionar usuarios'''
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Inyección de dependencias manual (en producción usar DI container)
            self.repository = DjangoUserRepository()
            self.event_publisher = RabbitMQEventPublisher()
        
        def create(self, request):
            '''
            POST /api/users/
            Crea un nuevo usuario
            '''
            # 1. Validar input
            serializer = CreateUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # 2. Ejecutar caso de uso
            try:
                use_case = CreateUserUseCase(self.repository, self.event_publisher)
                user = use_case.execute(
                    email=serializer.validated_data['email'],
                    username=serializer.validated_data['username'],
                    password=serializer.validated_data['password']
                )
                
                # 3. Serializar output
                output_serializer = UserSerializer(user)
                return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
            except UserAlreadyExists as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except InvalidEmail as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        def retrieve(self, request, pk=None):
            '''
            GET /api/users/{id}/
            Obtiene un usuario por ID
            '''
            try:
                use_case = GetUserUseCase(self.repository)
                user = use_case.execute(user_id=pk)
                
                serializer = UserSerializer(user)
                return Response(serializer.data)
            
            except UserNotFound:
                return Response(
                    {'error': f'Usuario {pk} no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        @action(detail=True, methods=['post'])
        def deactivate(self, request, pk=None):
            '''
            POST /api/users/{id}/deactivate/
            Desactiva un usuario
            '''
            serializer = DeactivateUserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            try:
                use_case = DeactivateUserUseCase(self.repository, self.event_publisher)
                user = use_case.execute(
                    user_id=pk,
                    reason=serializer.validated_data['reason']
                )
                
                output_serializer = UserSerializer(user)
                return Response(output_serializer.data)
            
            except UserNotFound:
                return Response(
                    {'error': f'Usuario {pk} no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )

💡 Los ViewSets son THIN CONTROLLERS: solo traducen HTTP a dominio y viceversa.
   TODA la lógica está en los casos de uso.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection


class HealthCheckView(APIView):
    """
    Endpoint de health check para verificar que el servicio está funcionando.
    
    GET /api/health/
    
    Returns:
        200: Servicio funcionando correctamente
        503: Servicio con problemas
    """
    
    def get(self, request):
        """Verifica estado del servicio y conectividad con la base de datos"""
        health_status = {
            'service': 'users-service',
            'status': 'healthy',
            'database': 'disconnected'
        }
        
        # Verificar conexión a base de datos
        try:
            connection.ensure_connection()
            health_status['database'] = 'connected'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['database'] = f'error: {str(e)}'
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(health_status, status=status.HTTP_200_OK)


# TODO: Implementar UserViewSet cuando se completen las capas de dominio y aplicación

