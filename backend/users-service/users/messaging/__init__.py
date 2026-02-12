"""
CAPA DE MENSAJERÍA - messaging/

📋 PROPÓSITO: Maneja la integración con otros microservicios mediante eventos asíncronos.

✅ Puede contener:
- Consumidores de eventos (listeners de RabbitMQ)
- Handlers de eventos recibidos de otros servicios
- Lógica de integración inter-servicios

✅ Puede depender de:
- application/ (ejecuta casos de uso)
- infrastructure/ (usa implementaciones concretas)
- pika, celery, etc.

🎯 FLUJO TÍPICO:
   RabbitMQ → Consumer → Handler → Use Case → Domain
   
   Ejemplo:
   1. El ticket-service publica: TicketAssigned(ticket_id, user_id)
   2. El consumer de users-service lo recibe
   3. El handler ejecuta un caso de uso: NotifyUserAboutAssignment
   4. El dominio procesa la lógica de notificación

💡 Esta capa permite arquitectura event-driven entre microservicios.
"""
