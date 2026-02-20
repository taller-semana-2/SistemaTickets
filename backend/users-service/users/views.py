"""
users/views.py — Presentation Layer (HTTP Controllers)

Thin controllers that delegate ALL logic to use cases.
Each action executes ONE use case.
Catches domain exceptions and converts them to HTTP responses.
Does NOT contain business logic.
"""

from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .application.use_cases import (
    RegisterUserCommand,
    LoginCommand,
    GetUsersByRoleCommand,
    RegisterUserUseCase,
    LoginUseCase,
    GetUsersByRoleUseCase,
)
from .infrastructure.repository import DjangoUserRepository
from .infrastructure.event_publisher import RabbitMQEventPublisher
from .infrastructure.cookie_utils import set_auth_cookies, clear_auth_cookies
from .serializers import RegisterUserSerializer, LoginSerializer
from .domain.exceptions import (
    UserAlreadyExists,
    InvalidEmail,
    InvalidUsername,
    InvalidUserData,
    UserNotFound,
)


class HealthCheckView(APIView):
    """
    Health check endpoint.

    GET /api/health/

    Returns:
        200: Service is healthy.
        503: Service is unhealthy.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """Verify service status and database connectivity."""
        health_status = {
            'service': 'users-service',
            'status': 'healthy',
            'database': 'disconnected',
        }

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
    ViewSet for user authentication.

    Endpoints:
    - POST /api/auth/          — Register a new user
    - POST /api/auth/login/    — Authenticate a user
    - GET  /api/auth/me/       — Get current authenticated user
    - POST /api/auth/logout/   — Clear auth cookies
    - GET  /api/auth/by-role/  — List users by role
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repository = DjangoUserRepository()
        self.event_publisher = RabbitMQEventPublisher()

    def get_permissions(self):
        """Allow public access to register, login, and logout."""
        if self.action in ('create', 'login', 'logout'):
            return [AllowAny()]
        return super().get_permissions()

    # ------------------------------------------------------------------
    # POST /api/auth/ — Register
    # ------------------------------------------------------------------

    def create(self, request):
        """
        Register a new user.

        Sets JWT tokens as HttpOnly cookies. The response body contains
        only user data — tokens are NEVER exposed in the JSON body.
        """
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            command = RegisterUserCommand(
                email=serializer.validated_data['email'],
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
            )

            use_case = RegisterUserUseCase(
                repository=self.repository,
                event_publisher=self.event_publisher,
            )

            auth_result = use_case.execute(command)
            user = auth_result['user']
            tokens = auth_result['tokens']

            user_data = {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': user.role.value,
                'is_active': user.is_active,
            }

            response = Response({'user': user_data}, status=status.HTTP_201_CREATED)
            return set_auth_cookies(response, tokens['access'], tokens['refresh'])

        except UserAlreadyExists as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (InvalidEmail, InvalidUsername, InvalidUserData) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ------------------------------------------------------------------
    # POST /api/auth/login/ — Login
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """
        Authenticate a user.

        Sets JWT tokens as HttpOnly cookies. The response body contains
        only user data — tokens are NEVER exposed in the JSON body.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            command = LoginCommand(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
            )

            use_case = LoginUseCase(repository=self.repository)
            auth_result = use_case.execute(command)
            user = auth_result['user']
            tokens = auth_result['tokens']

            user_data = {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'role': user.role.value,
                'is_active': user.is_active,
            }

            response = Response({'user': user_data}, status=status.HTTP_200_OK)
            return set_auth_cookies(response, tokens['access'], tokens['refresh'])

        except UserNotFound as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # ------------------------------------------------------------------
    # GET /api/auth/me/ — Current user info
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """
        Return the currently authenticated user's data.

        Reads the access_token from the HttpOnly cookie (handled by
        CookieJWTAuthentication). Requires authentication.
        """
        user = request.user

        return Response(
            {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'role': user.role if hasattr(user, 'role') else 'USER',
                'is_active': user.is_active,
            },
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # POST /api/auth/logout/ — Clear cookies
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """
        Log out by clearing authentication cookies.

        This endpoint is public so that even expired-token requests
        can still clear cookies.
        """
        response = Response({'detail': 'Sesión cerrada'}, status=status.HTTP_200_OK)
        return clear_auth_cookies(response)

    # ------------------------------------------------------------------
    # GET /api/auth/by-role/{role}/ — Users by role
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='by-role/(?P<role>[^/.]+)')
    def by_role(self, request, role=None):
        """
        List users filtered by role (ADMIN or USER).

        GET /api/auth/by-role/{role}/
        """
        try:
            command = GetUsersByRoleCommand(role=role)
            use_case = GetUsersByRoleUseCase(repository=self.repository)
            users = use_case.execute(command)

            users_data = [
                {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role.value,
                    'is_active': user.is_active,
                }
                for user in users
            ]

            return Response(users_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CookieTokenRefreshView(APIView):
    """
    Refresh JWT tokens by reading refresh_token from HttpOnly cookie.

    POST /api/auth/refresh/

    Reads the refresh_token cookie, generates a new access token (and
    optionally rotates the refresh token), and sets both as new cookies.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Refresh access token using the refresh_token cookie."""
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token no encontrado'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)
            new_refresh = str(refresh)

            response = Response(
                {'detail': 'Token renovado'}, status=status.HTTP_200_OK
            )
            return set_auth_cookies(response, new_access, new_refresh)

        except TokenError:
            response = Response(
                {'error': 'Refresh token inválido o expirado'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            return clear_auth_cookies(response)

