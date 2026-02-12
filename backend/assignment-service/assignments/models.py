"""
Importa modelos desde infrastructure para mantener compatibilidad con Django.
Django espera encontrar modelos en este archivo.
"""
from .infrastructure.django_models import TicketAssignmentModel as TicketAssignment

__all__ = ['TicketAssignment']
