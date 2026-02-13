"""
Entidad de dominio Assignment.
Contiene las reglas de negocio y validaciones del dominio.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Assignment:
    """
    Entidad de dominio que representa una asignación de ticket.
    
    Reglas de negocio:
    - Cada asignación pertenece a un único ticket
    - La prioridad debe ser válida (high, medium, low)
    - La fecha de asignación es inmutable una vez creada
    - assigned_to es una referencia lógica al usuario (sin foreign key)
    """
    ticket_id: str
    priority: str
    assigned_at: datetime
    id: Optional[int] = None
    assigned_to: Optional[str] = None
    
    VALID_PRIORITIES = ['high', 'medium', 'low']
    
    def __post_init__(self):
        """Valida la entidad al momento de creación"""
        self._validate()
    
    def _validate(self):
        """Ejecuta todas las validaciones de dominio"""
        if not self.ticket_id or not self.ticket_id.strip():
            raise ValueError("ticket_id es requerido y no puede estar vacío")
        
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"priority debe ser uno de {self.VALID_PRIORITIES}, "
                f"recibido: {self.priority}"
            )
    
    def change_priority(self, new_priority: str) -> None:
        """
        Cambia la prioridad de la asignación.
        Valida que la nueva prioridad sea válida.
        """
        if new_priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"priority debe ser uno de {self.VALID_PRIORITIES}, "
                f"recibido: {new_priority}"
            )
        self.priority = new_priority
