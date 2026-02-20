"""
Entidades de dominio - Representan conceptos del negocio con identidad única.
Contienen las reglas de negocio y son independientes del framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .events import DomainEvent, NotificationMarkedAsRead
from .exceptions import NotificationAlreadyRead


@dataclass
class Notification:
    """
    Entidad de dominio Notification.
    Representa una notificación con sus reglas de negocio encapsuladas.
    """
    
    # Atributos de la entidad
    id: Optional[int]
    ticket_id: str
    message: str
    sent_at: datetime
    read: bool = False
    user_id: str = ''
    response_id: Optional[int] = None
    
    # Lista de eventos de dominio generados por cambios en la entidad
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)
    
    def mark_as_read(self) -> None:
        """
        Marca la notificación como leída aplicando reglas de negocio.
        
        Reglas:
        - Una notificación puede marcarse como leída solo una vez
        - El cambio es idempotente (si ya está leída, no hace nada)
        - Cada cambio válido genera un evento de dominio
        
        Raises:
            NotificationAlreadyRead: Si la notificación ya está marcada como leída
        """
        # Idempotencia: Si ya está leída, no hacer nada
        if self.read:
            return
        
        # Marcar como leída
        self.read = True
        
        # Generar evento de dominio
        event = NotificationMarkedAsRead(
            occurred_at=datetime.now(),
            notification_id=self.id,
            ticket_id=self.ticket_id
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
