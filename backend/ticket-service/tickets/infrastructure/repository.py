"""
Django Repository - Implementación del repositorio usando Django ORM.
Adaptador que traduce entre el dominio y la persistencia.
"""

from typing import Optional, List

from ..domain.entities import Ticket as DomainTicket
from ..domain.repositories import TicketRepository
from ..models import Ticket as DjangoTicket


class DjangoTicketRepository(TicketRepository):
    """
    Implementación del repositorio usando Django ORM.
    Traduce entre entidades de dominio y modelos de Django.
    """
    
    def save(self, ticket: DomainTicket) -> DomainTicket:
        """
        Persiste un ticket en la base de datos (crear o actualizar).
        
        Args:
            ticket: Entidad de dominio
            
        Returns:
            La entidad con el ID asignado
        """
        if ticket.id:
            # Actualizar ticket existente
            django_ticket = DjangoTicket.objects.get(pk=ticket.id)
            django_ticket.title = ticket.title
            django_ticket.description = ticket.description
            django_ticket.status = ticket.status
            django_ticket.save(update_fields=['title', 'description', 'status'])
        else:
            # Crear nuevo ticket
            django_ticket = DjangoTicket.objects.create(
                title=ticket.title,
                description=ticket.description,
                status=ticket.status
            )
            ticket.id = django_ticket.id
        
        return ticket
    
    def find_by_id(self, ticket_id: int) -> Optional[DomainTicket]:
        """
        Busca un ticket por ID y lo convierte a entidad de dominio.
        
        Args:
            ticket_id: ID del ticket
            
        Returns:
            Entidad de dominio o None si no existe
        """
        try:
            django_ticket = DjangoTicket.objects.get(pk=ticket_id)
            return self._to_domain(django_ticket)
        except DjangoTicket.DoesNotExist:
            return None
    
    def find_all(self) -> List[DomainTicket]:
        """
        Obtiene todos los tickets ordenados por fecha de creación.
        
        Returns:
            Lista de entidades de dominio
        """
        django_tickets = DjangoTicket.objects.all().order_by('-created_at')
        return [self._to_domain(dt) for dt in django_tickets]
    
    def delete(self, ticket_id: int) -> None:
        """
        Elimina un ticket por ID.
        
        Args:
            ticket_id: ID del ticket a eliminar
        """
        DjangoTicket.objects.filter(pk=ticket_id).delete()
    
    @staticmethod
    def _to_domain(django_ticket: DjangoTicket) -> DomainTicket:
        """
        Convierte un modelo Django a entidad de dominio.
        
        Args:
            django_ticket: Modelo Django
            
        Returns:
            Entidad de dominio
        """
        return DomainTicket(
            id=django_ticket.id,
            title=django_ticket.title,
            description=django_ticket.description,
            status=django_ticket.status,
            created_at=django_ticket.created_at
        )
