"""
ViewSet refactorizado para usar casos de uso.
No contiene lógica de negocio, solo orquesta la ejecución de casos de uso.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TicketAssignment
from .serializers import TicketAssignmentSerializer
from .infrastructure.repository import DjangoAssignmentRepository
from .infrastructure.messaging.event_publisher import RabbitMQEventPublisher
from .application.use_cases.create_assignment import CreateAssignment
from .application.use_cases.reassign_ticket import ReassignTicket


class TicketAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar asignaciones de tickets.
    
    Refactorizado para:
    - No acceder directamente al ORM en operaciones de negocio
    - Delegar lógica de negocio a casos de uso
    - Mantener compatibilidad con Django REST Framework
    """
    queryset = TicketAssignment.objects.all().order_by('-assigned_at')
    serializer_class = TicketAssignmentSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository = DjangoAssignmentRepository()
        self.event_publisher = RabbitMQEventPublisher()
    
    def create(self, request, *args, **kwargs):
        """
        Crea una nueva asignación usando el caso de uso.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ticket_id = serializer.validated_data['ticket_id']
        priority = serializer.validated_data['priority']
        
        use_case = CreateAssignment(self.repository, self.event_publisher)
        
        try:
            assignment = use_case.execute(ticket_id=ticket_id, priority=priority)
            
            response_serializer = self.get_serializer(
                TicketAssignment.objects.get(id=assignment.id)
            )
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='reassign')
    def reassign(self, request):
        """
        Reasigna un ticket (cambia su prioridad).
        
        Endpoint: POST /assignments/reassign/
        Body: {"ticket_id": "...", "priority": "..."}
        """
        ticket_id = request.data.get('ticket_id')
        new_priority = request.data.get('priority')
        
        if not ticket_id or not new_priority:
            return Response(
                {'error': 'ticket_id y priority son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        use_case = ReassignTicket(self.repository, self.event_publisher)
        
        try:
            assignment = use_case.execute(
                ticket_id=ticket_id,
                new_priority=new_priority
            )
            
            response_serializer = self.get_serializer(
                TicketAssignment.objects.get(id=assignment.id)
            )
            
            return Response(response_serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

