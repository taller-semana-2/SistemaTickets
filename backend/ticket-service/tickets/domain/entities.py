"""
Entidades de dominio - Representan conceptos del negocio con identidad única.
Contienen las reglas de negocio y son independientes del framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .events import DomainEvent, TicketCreated, TicketStatusChanged, TicketPriorityChanged
from .exceptions import TicketAlreadyClosed


@dataclass
class Ticket:
    """
    Entidad de dominio Ticket.
    Representa un ticket con sus reglas de negocio encapsuladas.
    """
    
    # Estados válidos del ticket
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    
    # Atributos de la entidad
    id: Optional[int]
    title: str
    description: str
    status: str
    user_id: str
    created_at: datetime
    priority: str = "Unassigned"  # Prioridad por defecto
    
    # Lista de eventos de dominio generados por cambios en la entidad
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)
    
    def __post_init__(self):
        """Validación de estado inicial."""
        if self.status not in [self.OPEN, self.IN_PROGRESS, self.CLOSED]:
            raise ValueError(f"Estado inválido: {self.status}")
    
    def change_status(self, new_status: str) -> None:
        """
        Cambia el estado del ticket aplicando reglas de negocio.
        
        Reglas:
        - No se puede cambiar el estado de un ticket cerrado
        - El cambio es idempotente (si ya tiene ese estado, no hace nada)
        - Cada cambio válido genera un evento de dominio
        
        Args:
            new_status: Nuevo estado del ticket
            
        Raises:
            TicketAlreadyClosed: Si el ticket está cerrado
            ValueError: Si el nuevo estado no es válido
        """
        # Validar que el nuevo estado sea válido
        if new_status not in [self.OPEN, self.IN_PROGRESS, self.CLOSED]:
            raise ValueError(f"Estado inválido: {new_status}")
        
        # Regla: No se puede cambiar el estado de un ticket cerrado
        if self.status == self.CLOSED:
            raise TicketAlreadyClosed(self.id)
        
        # Idempotencia: Si el estado es el mismo, no hacer nada
        if self.status == new_status:
            return
        
        # Cambiar estado
        old_status = self.status
        self.status = new_status
        
        # Generar evento de dominio
        event = TicketStatusChanged(
            occurred_at=datetime.now(),
            ticket_id=self.id,
            old_status=old_status,
            new_status=new_status
        )
        self._domain_events.append(event)
    
    def change_priority(self, new_priority: str) -> None:
        """
        Cambia la prioridad del ticket aplicando reglas de negocio.
        
        Reglas:
        - El cambio es idempotente (si ya tiene esa prioridad, no hace nada)
        - Cada cambio válido genera un evento de dominio
        
        Args:
            new_priority: Nueva prioridad del ticket
        """
        # Idempotencia: Si la prioridad es la misma, no hacer nada
        if self.priority == new_priority:
            return
        
        # Cambiar prioridad
        old_priority = self.priority
        self.priority = new_priority
        
        # Generar evento de dominio
        event = TicketPriorityChanged(
            occurred_at=datetime.now(),
            ticket_id=self.id,
            old_priority=old_priority,
            new_priority=new_priority
        )
        self._domain_events.append(event)
    
    def collect_domain_events(self) -> List[DomainEvent]:
        """
        Recolecta y limpia los eventos de dominio generados.
        Se usa para publicar eventos después de persistir cambios.
        
        Returns:
            Lista de eventos de dominio
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
    
    @staticmethod
    def create(title: str, description: str, user_id: str) -> "Ticket":
        """
        Crea un nuevo ticket en estado OPEN (método factory).
        
        Args:
            title: Título del ticket
            description: Descripción del ticket
            user_id: ID del usuario que crea el ticket
            
        Returns:
            Nueva instancia de Ticket
        """
        ticket = Ticket(
            id=None,  # El ID se asigna al persistir
            title=title,
            description=description,
            status=Ticket.OPEN,
            user_id=user_id,
            created_at=datetime.now()
        )
        
        # Nota: El evento TicketCreated se genera al persistir
        # porque necesitamos el ID asignado por la BD
        
        return ticket
