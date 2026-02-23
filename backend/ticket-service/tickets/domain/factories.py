"""
Factory - Crea instancias de entidades de dominio asegurando validez.
"""

import re
from datetime import datetime

from .entities import Ticket
from .exceptions import InvalidTicketData, DangerousInputError


# Patrón regex para detectar CUALQUIER tag HTML
# Rechaza cualquier contenido entre < y >, bloqueando todo tipo de HTML/scripts
_DANGEROUS_PATTERN = re.compile(r"<[^>]+>")


def _contains_dangerous_html(value: str) -> bool:
    """
    Verifica si el valor contiene tags HTML.
    
    Rechaza CUALQUIER tag HTML para prevenir XSS. Esto incluye:
    - Tags de script: <script>, <iframe>, <object>
    - Tags con event handlers: <img onerror>, <div onclick>
    - Cualquier otro tag HTML: <a>, <p>, <span>, etc.
    
    Estrategia: Para un sistema de tickets no necesitamos permitir HTML.
    Es más seguro rechazar todo que intentar detectar casos específicos.
    
    Args:
        value: String a validar
        
    Returns:
        True si contiene algún tag HTML, False en caso contrario
    """
    return bool(_DANGEROUS_PATTERN.search(value))


class TicketFactory:
    """
    Factory para crear tickets válidos.
    Aplica validaciones y reglas de creación.
    """
    
    @staticmethod
    def create(title: str, description: str, user_id: str) -> Ticket:
        """
        Crea un nuevo ticket validando los datos de entrada.
        
        Args:
            title: Título del ticket (no puede estar vacío)
            description: Descripción del ticket (no puede estar vacía)
            user_id: ID del usuario que crea el ticket (no puede estar vacío)
            
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
        
        if not user_id or not user_id.strip():
            raise InvalidTicketData("El ID de usuario no puede estar vacío")
        
        # Validación de seguridad: prevenir Stored XSS
        if _contains_dangerous_html(title):
            raise DangerousInputError("título")
        
        if _contains_dangerous_html(description):
            raise DangerousInputError("descripción")
        
        # Crear ticket usando el método factory de la entidad
        return Ticket.create(
            title=title.strip(),
            description=description.strip(),
            user_id=user_id.strip()
        )
