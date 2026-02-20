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
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import connection

from .application.use_cases import (
    RegisterUserCommand,
    LoginCommand,
    GetUsersByRoleCommand,
    RegisterUserUseCase,
    LoginUseCase,
    GetUsersByRoleUseCase
)
from .infrastructure.repository import DjangoUserRepository
from .infrastructure.event_publisher import RabbitMQEventPublisher
from .serializers import (
    RegisterUserSerializer,
    LoginSerializer,
    AuthResponseSerializer
)
from .domain.exceptions import (
    UserAlreadyExists,
    InvalidEmail,
    InvalidUsername,
    InvalidUserData,
    UserNotFound
)


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


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet para autenticación de usuarios.
    
    Endpoints:
    - POST /api/auth/register/ - Registrar un nuevo usuario
    - POST /api/auth/login/ - Autenticar un usuario
    """

    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Inyección de dependencias
        self.repository = DjangoUserRepository()
        self.event_publisher = RabbitMQEventPublisher()

    def get_permissions(self):
        """Permite acceso público solo a register y login."""
        if self.action in ('create', 'login'):
            return [AllowAny()]
        return super().get_permissions()
    
    def create(self, request):
        """
        POST /api/auth/register/
        Registrar un nuevo usuario
        """
        # 1. Validar input
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2. Ejecutar caso de uso
        try:
            command = RegisterUserCommand(
                email=serializer.validated_data['email'],
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
            )
            
            use_case = RegisterUserUseCase(
                repository=self.repository,
                event_publisher=self.event_publisher
            )
            
            auth_result = use_case.execute(command)
            user = auth_result['user']
            tokens = auth_result['tokens']
            
            # 3. Serializar output con contrato de autenticación
            output_serializer = AuthResponseSerializer({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role.value,
                    'is_active': user.is_active,
                },
                'tokens': {
                    'access': tokens['access'],
                    'refresh': tokens['refresh'],
                }
            })
            
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        
        except UserAlreadyExists as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (InvalidEmail, InvalidUsername, InvalidUserData) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def login(self, request):
        """
        POST /api/auth/login/
        Autenticar un usuario
        """
        # 1. Validar input
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2. Ejecutar caso de uso
        try:
            command = LoginCommand(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            use_case = LoginUseCase(repository=self.repository)
            auth_result = use_case.execute(command)
            user = auth_result['user']
            tokens = auth_result['tokens']
            
            # 3. Serializar output con contrato de autenticación
            output_serializer = AuthResponseSerializer({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role.value,
                    'is_active': user.is_active,
                },
                'tokens': {
                    'access': tokens['access'],
                    'refresh': tokens['refresh'],
                }
            })
            
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        
        except UserNotFound as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='by-role/(?P<role>[^/.]+)')
    def by_role(self, request, role=None):
        """
        GET /api/auth/by-role/{role}/
        Obtener usuarios por rol (ADMIN o USER)
        """
        try:
            command = GetUsersByRoleCommand(role=role)
            use_case = GetUsersByRoleUseCase(repository=self.repository)
            users = use_case.execute(command)
            
            # Serializar lista de usuarios
            users_data = [
                {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role.value,
                    'is_active': user.is_active
                }
                for user in users
            ]
            
            return Response(users_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# TODO: Implementar UserViewSet cuando se completen las capas de dominio y aplicación

