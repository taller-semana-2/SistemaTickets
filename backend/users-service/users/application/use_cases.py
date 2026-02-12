"""
Use Cases (Comandos) - Casos de uso que orquestan operaciones de dominio.
Cada caso de uso representa una operación de negocio completa.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..domain.entities import User
from ..domain.factories import UserFactory
from ..domain.repositories import UserRepository
from ..domain.event_publisher import EventPublisher
from ..domain.events import UserCreated, UserDeactivated
from ..domain.exceptions import UserAlreadyExists, UserNotFound


@dataclass
class CreateUserCommand:
    """Comando: Crear un nuevo usuario."""
    email: str
    username: str
    password: str


@dataclass
class DeactivateUserCommand:
    """Comando: Desactivar un usuario."""
    user_id: str
    reason: Optional[str] = None


@dataclass
class ChangeUserEmailCommand:
    """Comando: Cambiar el email de un usuario."""
    user_id: str
    new_email: str


class CreateUserUseCase:
    """
    Caso de uso: Crear un nuevo usuario.
    
    Responsabilidades:
    1. Validar que el email no exista
    2. Crear la entidad mediante factory (validaciones)
    3. Persistir el usuario usando el repositorio
    4. Generar y publicar eventos de dominio
    """
    
    def __init__(
        self,
        repository: UserRepository,
        event_publisher: EventPublisher,
        factory: UserFactory = None
    ):
        """
        Inyección de dependencias (DIP).
        
        Args:
            repository: Repositorio para persistencia
            event_publisher: Publicador de eventos
            factory: Factory para crear usuarios (opcional)
        """
        self.repository = repository
        self.event_publisher = event_publisher
        self.factory = factory or UserFactory()
    
    def execute(self, command: CreateUserCommand) -> User:
        """
        Ejecuta el caso de uso de creación de usuario.
        
        Args:
            command: Comando con los datos del usuario
            
        Returns:
            El usuario creado y persistido
            
        Raises:
            UserAlreadyExists: Si el email ya está registrado
            InvalidEmail: Si el email no es válido
            InvalidUsername: Si el username no cumple requisitos
            InvalidUserData: Si el password es muy corto
        """
        # 1. Validar que el email no exista
        if self.repository.exists_by_email(command.email):
            raise UserAlreadyExists(command.email)
        
        # 2. Crear entidad de dominio usando factory (valida)
        user = self.factory.create(
            email=command.email,
            username=command.username,
            password=command.password
        )
        
        # 3. Persistir el usuario
        user = self.repository.save(user)
        
        # 4. Generar evento de dominio (ahora que tenemos el ID)
        event = UserCreated(
            occurred_at=datetime.now(),
            user_id=user.id,
            email=user.email,
            username=user.username
        )
        
        # 5. Publicar evento
        self.event_publisher.publish(event, 'user.created')
        
        return user


class DeactivateUserUseCase:
    """
    Caso de uso: Desactivar un usuario.
    
    Responsabilidades:
    1. Obtener el usuario del repositorio
    2. Aplicar la desactivación (reglas de negocio)
    3. Persistir el cambio
    4. Publicar eventos de dominio generados
    """
    
    def __init__(
        self,
        repository: UserRepository,
        event_publisher: EventPublisher
    ):
        """
        Inyección de dependencias (DIP).
        
        Args:
            repository: Repositorio para persistencia
            event_publisher: Publicador de eventos
        """
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, command: DeactivateUserCommand) -> User:
        """
        Ejecuta el caso de uso de desactivación de usuario.
        
        Args:
            command: Comando con el ID del usuario y razón opcional
            
        Returns:
            El usuario desactivado
            
        Raises:
            UserNotFound: Si el usuario no existe
            UserAlreadyInactive: Si el usuario ya está inactivo
        """
        # 1. Obtener el usuario
        user = self.repository.find_by_id(command.user_id)
        
        if not user:
            raise UserNotFound(command.user_id)
        
        # 2. Aplicar desactivación (reglas de negocio en la entidad)
        user.deactivate(reason=command.reason)
        
        # 3. Persistir el cambio
        user = self.repository.save(user)
        
        # 4. Recolectar y publicar eventos de dominio generados
        events = user.collect_domain_events()
        for event in events:
            self.event_publisher.publish(event, 'user.deactivated')
        
        return user


class ChangeUserEmailUseCase:
    """
    Caso de uso: Cambiar el email de un usuario.
    
    Responsabilidades:
    1. Obtener el usuario del repositorio
    2. Validar que el nuevo email no exista
    3. Aplicar el cambio de email (reglas de negocio)
    4. Persistir el cambio
    5. Publicar eventos de dominio generados
    """
    
    def __init__(
        self,
        repository: UserRepository,
        event_publisher: EventPublisher
    ):
        """
        Inyección de dependencias (DIP).
        
        Args:
            repository: Repositorio para persistencia
            event_publisher: Publicador de eventos
        """
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, command: ChangeUserEmailCommand) -> User:
        """
        Ejecuta el caso de uso de cambio de email.
        
        Args:
            command: Comando con el ID del usuario y el nuevo email
            
        Returns:
            El usuario con el email actualizado
            
        Raises:
            UserNotFound: Si el usuario no existe
            UserAlreadyExists: Si el nuevo email ya está en uso
            InvalidEmail: Si el nuevo email no es válido
        """
        # 1. Obtener el usuario
        user = self.repository.find_by_id(command.user_id)
        
        if not user:
            raise UserNotFound(command.user_id)
        
        # 2. Validar que el nuevo email no exista (si es diferente)
        if command.new_email.lower() != user.email.lower():
            if self.repository.exists_by_email(command.new_email):
                raise UserAlreadyExists(command.new_email)
        
        # 3. Aplicar cambio de email (reglas de negocio en la entidad)
        user.change_email(command.new_email)
        
        # 4. Persistir el cambio
        user = self.repository.save(user)
        
        # 5. Recolectar y publicar eventos de dominio generados
        events = user.collect_domain_events()
        for event in events:
            self.event_publisher.publish(event, 'user.email_changed')
        
        return user


class GetUserUseCase:
    """
    Caso de uso: Obtener un usuario por ID.
    """
    
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    def execute(self, user_id: str) -> User:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            El usuario encontrado
            
        Raises:
            UserNotFound: Si el usuario no existe
        """
        user = self.repository.find_by_id(user_id)
        
        if not user:
            raise UserNotFound(user_id)
        
        return user


class ListUsersUseCase:
    """
    Caso de uso: Listar todos los usuarios.
    """
    
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    def execute(self):
        """
        Obtiene todos los usuarios.
        
        Returns:
            Lista de usuarios
        """
        return self.repository.find_all()
