"""
Entidades de dominio - Representan conceptos del negocio con identidad única.
Contienen las reglas de negocio y son independientes del framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .events import DomainEvent, TicketCreated, TicketStatusChanged, TicketPriorityChanged
from .exceptions import TicketAlreadyClosed, InvalidPriorityTransition, InvalidTicketStateTransition


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
    
    # Prioridades válidas del ticket
    PRIORITY_UNASSIGNED = "Unassigned"
    PRIORITY_LOW = "Low"
    PRIORITY_MEDIUM = "Medium"
    PRIORITY_HIGH = "High"
    
    # Constante con todas las prioridades válidas (para validación)
    VALID_PRIORITIES = [
        PRIORITY_UNASSIGNED,
        PRIORITY_LOW,
        PRIORITY_MEDIUM,
        PRIORITY_HIGH
    ]
    
    # Atributos de la entidad
    id: Optional[int]
    title: str
    description: str
    status: str
    user_id: str
    created_at: datetime
    priority: str = "Unassigned"  # Prioridad por defecto: Unassigned
    
    # Lista de eventos de dominio generados por cambios en la entidad
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)
    
    def __post_init__(self):
        """Validación de estado inicial."""
        if self.status not in [self.OPEN, self.IN_PROGRESS, self.CLOSED]:
            raise ValueError(f"Estado inválido: {self.status}")
    
    def _validate_state_transition(self, new_status: str) -> None:
        """
        Valida que la transición de estado sea válida.
        
        Transiciones válidas:
        - OPEN → IN_PROGRESS
        - IN_PROGRESS → CLOSED
        - OPEN → OPEN, IN_PROGRESS → IN_PROGRESS, CLOSED → CLOSED (idempotentes)
        
        Transiciones inválidas:
        - OPEN → CLOSED (debe pasar por IN_PROGRESS primero)
        - Cualquier transición desde CLOSED
        
        Args:
            new_status: Nuevo status a validar
            
        Raises:
            InvalidTicketStateTransition: Si la transición no es válida
        """
        # Transición inválida: OPEN → CLOSED tiene que pasar por IN_PROGRESS
        if self.status == self.OPEN and new_status == self.CLOSED:
            raise InvalidTicketStateTransition(
                self.status,
                new_status
            )
    
    def change_status(self, new_status: str) -> None:
        """
        Cambia el estado del ticket aplicando reglas de negocio.
        
        Transiciones válidas:
        ┌─────────────┬──────────────┬─────────┐
        │ Estado      │ Estado nuevo │ Válida  │
        ├─────────────┼──────────────┼─────────┤
        │ OPEN        │ OPEN         │ Sí (no-op) │
        │ OPEN        │ IN_PROGRESS  │ Sí      │
        │ OPEN        │ CLOSED       │ No      │
        │ IN_PROGRESS │ IN_PROGRESS  │ Sí (no-op) │
        │ IN_PROGRESS │ CLOSED       │ Sí      │
        │ CLOSED      │ *            │ No      │
        └─────────────┴──────────────┴─────────┘
        
        Args:
            new_status: Nuevo estado del ticket
            
        Raises:
            InvalidTicketStateTransition: Si la transición no es válida
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
        
        # Validar que la transición sea válida (debe ocurrir antes de cambiar estado)
        self._validate_state_transition(new_status)
        
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
    
    def _validate_priority_value(self, new_priority: str) -> None:
        """
        Valida que la prioridad sea un valor permitido.
        
        Args:
            new_priority: Prioridad a validar
            
        Raises:
            ValueError: Si la prioridad no es válida
        """
        if new_priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"Prioridad inválida: {new_priority}. "
                f"Valores válidos: {', '.join(self.VALID_PRIORITIES)}"
            )
    
    def _validate_priority_transition(self, new_priority: str) -> None:
        """
        Valida que la transición de prioridad sea permitida.
        
        Regla: No se puede volver a Unassigned una vez asignada otra prioridad.
        
        Args:
            new_priority: Nueva prioridad objetivo
            
        Raises:
            InvalidPriorityTransition: Si la transición no es válida
        """
        if (self.priority != self.PRIORITY_UNASSIGNED and 
            new_priority == self.PRIORITY_UNASSIGNED):
            raise InvalidPriorityTransition(
                self.priority,
                new_priority,
                "no se puede volver a Unassigned una vez asignada otra prioridad"
            )
    
    def change_priority(self, new_priority: str) -> None:
        """
        Cambia la prioridad del ticket aplicando reglas de negocio.
        
        Reglas de negocio (MVP):
        1. Solo valores válidos: Unassigned, Low, Medium, High
        2. No se puede volver a Unassigned una vez asignada otra prioridad
        3. El cambio es idempotente (si ya tiene esa prioridad, no hace nada)
        4. Cada cambio válido genera un evento de dominio TicketPriorityChanged
        
        Args:
            new_priority: Nueva prioridad del ticket
            
        Raises:
            InvalidPriorityTransition: Si la transición no es válida
            ValueError: Si la prioridad no es un valor válido
        """
        # Validar que la nueva prioridad sea válida
        self._validate_priority_value(new_priority)
        
        # Idempotencia: Si la prioridad es la misma, no hacer nada
        if self.priority == new_priority:
            return
        
        # Regla de negocio: No se puede volver a Unassigned una vez asignada prioridad
        self._validate_priority_transition(new_priority)
        
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
