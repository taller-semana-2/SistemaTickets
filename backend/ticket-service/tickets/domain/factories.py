"""
Factory - Crea instancias de entidades de dominio asegurando validez.
"""

from datetime import datetime

from .entities import Ticket
from .exceptions import InvalidTicketData


class TicketFactory:
    """
    Factory para crear tickets válidos.
    Aplica validaciones y reglas de creación.
    """
    
    @staticmethod
    def create(title: str, description: str) -> Ticket:
        """
        Crea un nuevo ticket validando los datos de entrada.
        
        Args:
            title: Título del ticket (no puede estar vacío)
            description: Descripción del ticket (no puede estar vacía)
            
        Returns:
            Nueva instancia de Ticket en estado OPEN
            
        Raises:
            InvalidTicketData: Si los datos no son válidos
        """
        # Validaciones de negocio
        if not title or not title.strip():
            raise InvalidTicketData("El título no puede estar vacío")
        
        if not description or not description.strip():
            raise InvalidTicketData("La descripción no puede estar vacía")
        
        # Crear ticket usando el método factory de la entidad
        return Ticket.create(
            title=title.strip(),
            description=description.strip()
        )
