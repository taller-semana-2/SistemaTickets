"""
Use Cases (Comandos) - Casos de uso que orquestan operaciones de dominio.
Cada caso de uso representa una operación de negocio completa.
"""

from dataclasses import dataclass
from datetime import datetime

from ..domain.entities import Ticket
from ..domain.factories import TicketFactory
from ..domain.repositories import TicketRepository
from ..domain.event_publisher import EventPublisher
from ..domain.events import TicketCreated, TicketStatusChanged, TicketResponseAdded
from ..domain.exceptions import TicketAlreadyClosed, DomainException


@dataclass
class CreateTicketCommand:
    """Comando: Crear un nuevo ticket."""
    title: str
    description: str
    user_id: str


@dataclass
class ChangeTicketStatusCommand:
    """Comando: Cambiar el estado de un ticket."""
    ticket_id: int
    new_status: str


@dataclass
class ChangeTicketPriorityCommand:
    """Comando: Cambiar la prioridad de un ticket."""
    ticket_id: int
    new_priority: str


class CreateTicketUseCase:
    """
    Caso de uso: Crear un nuevo ticket.
    
    Responsabilidades:
    1. Validar y crear la entidad mediante factory
    2. Persistir el ticket usando el repositorio
    3. Generar y publicar eventos de dominio
    """
    
    def __init__(
        self,
        repository: TicketRepository,
        event_publisher: EventPublisher,
        factory: TicketFactory = None
    ):
        """
        Inyección de dependencias (DIP).
        
        Args:
            repository: Repositorio para persistencia
            event_publisher: Publicador de eventos
            factory: Factory para crear tickets (opcional)
        """
        self.repository = repository
        self.event_publisher = event_publisher
        self.factory = factory or TicketFactory()
    
    def execute(self, command: CreateTicketCommand) -> Ticket:
        """
        Ejecuta el caso de uso de creación de ticket.
        
        Args:
            command: Comando con los datos del ticket
            
        Returns:
            El ticket creado y persistido
            
        Raises:
            InvalidTicketData: Si los datos no son válidos
        """
        # 1. Crear entidad de dominio usando factory (valida)
        ticket = self.factory.create(
            title=command.title,
            description=command.description,
            user_id=command.user_id
        )
        
        # 2. Persistir el ticket
        ticket = self.repository.save(ticket)
        
        # 3. Generar evento de dominio (ahora que tenemos el ID)
        occurred_at = datetime.now()
        event = TicketCreated(
            occurred_at=occurred_at,
            ticket_id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status,
            user_id=ticket.user_id
        )
        
        # 4. Publicar evento
        self.event_publisher.publish(event)
        
        return ticket


class ChangeTicketStatusUseCase:
    """
    Caso de uso: Cambiar el estado de un ticket.
    
    Responsabilidades:
    1. Obtener el ticket del repositorio
    2. Aplicar el cambio de estado (reglas de negocio)
    3. Persistir el cambio
    4. Publicar eventos de dominio generados
    """
    
    def __init__(
        self,
        repository: TicketRepository,
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
    
    def execute(self, command: ChangeTicketStatusCommand) -> Ticket:
        """
        Ejecuta el caso de uso de cambio de estado.
        
        Args:
            command: Comando con el ID del ticket y el nuevo estado
            
        Returns:
            El ticket actualizado
            
        Raises:
            ValueError: Si el ticket no existe o el estado es inválido
            TicketAlreadyClosed: Si el ticket está cerrado
        """
        # 1. Obtener el ticket
        ticket = self.repository.find_by_id(command.ticket_id)
        
        if not ticket:
            raise ValueError(f"Ticket {command.ticket_id} no encontrado")
        
        # 2. Aplicar cambio de estado (reglas de negocio en la entidad)
        ticket.change_status(command.new_status)
        
        # 3. Persistir el cambio
        ticket = self.repository.save(ticket)
        
        # 4. Recolectar y publicar eventos de dominio generados
        events = ticket.collect_domain_events()
        for event in events:
            self.event_publisher.publish(event)
        
        return ticket


class ChangeTicketPriorityUseCase:
    """
    Caso de uso: Cambiar la prioridad de un ticket.
    
    Responsabilidades:
    1. Obtener el ticket del repositorio
    2. Aplicar el cambio de prioridad (reglas de negocio)
    3. Persistir el cambio
    4. Publicar eventos de dominio generados
    """
    
    def __init__(
        self,
        repository: TicketRepository,
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
    
    def execute(self, command: ChangeTicketPriorityCommand) -> Ticket:
        """
        Ejecuta el caso de uso de cambio de prioridad.
        
        Args:
            command: Comando con el ID del ticket y la nueva prioridad
            
        Returns:
            El ticket actualizado
            
        Raises:
            ValueError: Si el ticket no existe
        """
        user_role = getattr(command, "user_role", None)
        if user_role is not None and user_role != "Administrador":
            raise DomainException("Permiso insuficiente para cambiar la prioridad")

        # 1. Obtener el ticket
        ticket = self.repository.find_by_id(command.ticket_id)
        
        if not ticket:
            raise ValueError(f"Ticket {command.ticket_id} no encontrado")
        
        # 2. Aplicar cambio de prioridad (reglas de negocio en la entidad)
        ticket.change_priority(command.new_priority)
        
        # 3. Persistir el cambio
        ticket = self.repository.save(ticket)
        
        # 4. Recolectar y publicar eventos de dominio generados
        events = ticket.collect_domain_events()
        for event in events:
            self.event_publisher.publish(event)
        
        return ticket


@dataclass
class AddTicketResponseCommand:
    """Comando: Agregar una respuesta a un ticket."""
    ticket_id: int
    text: str
    admin_id: str
    response_id: int = 0  # Inyectado desde la capa de infraestructura tras persistir


class AddTicketResponseUseCase:
    """
    Caso de uso: Agregar una respuesta de admin a un ticket.

    Responsabilidades:
    1. Obtener el ticket del repositorio
    2. Aplicar la operación de dominio (add_response)
    3. Persistir el cambio
    4. Generar y publicar eventos de dominio
    """

    def __init__(
        self,
        repository: TicketRepository,
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

    def execute(self, command: AddTicketResponseCommand) -> Ticket:
        """
        Ejecuta el caso de uso de agregar respuesta.

        Args:
            command: Comando con ticket_id, text y admin_id

        Returns:
            El ticket actualizado

        Raises:
            ValueError: Si el ticket no existe
            TicketAlreadyClosed: Si el ticket está cerrado
            EmptyResponseError: Si el texto está vacío
        """
        # 1. Obtener el ticket
        ticket = self.repository.find_by_id(command.ticket_id)

        if not ticket:
            raise ValueError(f"Ticket {command.ticket_id} no encontrado")

        # 2. Aplicar la operación de dominio (add_response)
        ticket.add_response(command.text, command.admin_id)

        # 3. Persistir el cambio
        self.repository.save(ticket)

        # 4. Generar y publicar evento de dominio con el response_id real
        event = TicketResponseAdded(
            occurred_at=datetime.now(),
            ticket_id=ticket.id,
            response_id=command.response_id,
            admin_id=command.admin_id,
            response_text=command.text,
            user_id=ticket.user_id,
        )
        self.event_publisher.publish(event)

        return ticket
