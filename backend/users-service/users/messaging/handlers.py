"""
messaging/handlers.py

🎯 PROPÓSITO:
Maneja eventos recibidos de otros microservicios ejecutando casos de uso.

📐 ESTRUCTURA:
- Un handler por tipo de evento
- Cada handler transforma el evento en parámetros de caso de uso
- Ejecuta el caso de uso correspondiente
- Maneja errores de dominio

✅ EJEMPLO de lo que DEBE ir aquí:
    from users.application.use_cases import NotifyUserAboutAssignmentUseCase
    from users.infrastructure.repository import DjangoUserRepository
    from users.infrastructure.event_publisher import RabbitMQEventPublisher
    
    class TicketAssignedHandler:
        '''Maneja el evento: Un ticket fue asignado a un usuario'''
        
        def __init__(self):
            # Inyectar dependencias
            self.repository = DjangoUserRepository()
            self.event_publisher = RabbitMQEventPublisher()
            self.use_case = NotifyUserAboutAssignmentUseCase(
                self.repository,
                self.event_publisher
            )
        
        def handle(self, event_data: dict):
            '''
            Procesa el evento TicketAssigned.
            
            event_data ejemplo:
            {
                "ticket_id": "123",
                "user_id": "456",
                "ticket_title": "Bug en login",
                "occurred_at": "2026-02-12T10:00:00"
            }
            '''
            try:
                # Extraer datos del evento
                ticket_id = event_data['ticket_id']
                user_id = event_data['user_id']
                ticket_title = event_data.get('ticket_title', 'Sin título')
                
                # Ejecutar caso de uso
                self.use_case.execute(
                    user_id=user_id,
                    ticket_id=ticket_id,
                    ticket_title=ticket_title
                )
                
                print(f"[✓] Usuario {user_id} notificado sobre ticket {ticket_id}")
            
            except Exception as e:
                print(f"[ERROR] Manejando TicketAssigned: {e}")
                # En producción: enviar a dead-letter queue o log centralizado
    
    class TicketClosedHandler:
        '''Maneja el evento: Un ticket fue cerrado'''
        
        def handle(self, event_data: dict):
            # Similar al anterior...
            pass

💡 Los handlers son el PUENTE entre eventos externos y la lógica de tu servicio.
   Traducen eventos en comandos de tu dominio.
"""
