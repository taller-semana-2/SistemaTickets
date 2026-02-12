# Guía de Uso - Assignment Service (DDD)

## Ejemplos de Uso

### 1. Crear una Asignación vía API

```bash
# Crear nueva asignación
curl -X POST http://localhost:8000/assignments/ \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "priority": "high"
  }'

# Respuesta
{
  "id": 1,
  "ticket_id": "TKT-001",
  "priority": "high",
  "assigned_at": "2026-02-11T10:30:00Z"
}
```

### 2. Reasignar un Ticket

```bash
# Cambiar prioridad de un ticket existente
curl -X POST http://localhost:8000/assignments/reassign/ \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "priority": "low"
  }'

# Respuesta
{
  "id": 1,
  "ticket_id": "TKT-001",
  "priority": "low",
  "assigned_at": "2026-02-11T10:30:00Z"
}
```

### 3. Listar Asignaciones

```bash
# Obtener todas las asignaciones
curl http://localhost:8000/assignments/

# Respuesta
[
  {
    "id": 1,
    "ticket_id": "TKT-001",
    "priority": "high",
    "assigned_at": "2026-02-11T10:30:00Z"
  },
  {
    "id": 2,
    "ticket_id": "TKT-002",
    "priority": "medium",
    "assigned_at": "2026-02-11T09:15:00Z"
  }
]
```

### 4. Obtener una Asignación Específica

```bash
# GET por ID
curl http://localhost:8000/assignments/1/

# Respuesta
{
  "id": 1,
  "ticket_id": "TKT-001",
  "priority": "high",
  "assigned_at": "2026-02-11T10:30:00Z"
}
```

## Uso Programático desde Django

### Crear Asignación (Use Case)

```python
from assignments.infrastructure.repository import DjangoAssignmentRepository
from assignments.infrastructure.messaging.event_publisher import RabbitMQEventPublisher
from assignments.application.use_cases.create_assignment import CreateAssignment

# Configurar dependencias
repository = DjangoAssignmentRepository()
event_publisher = RabbitMQEventPublisher()

# Ejecutar caso de uso
use_case = CreateAssignment(repository, event_publisher)
assignment = use_case.execute(
    ticket_id="TKT-003",
    priority="medium"
)

print(f"Asignación creada: {assignment.id}")
```

### Reasignar Ticket (Use Case)

```python
from assignments.infrastructure.repository import DjangoAssignmentRepository
from assignments.infrastructure.messaging.event_publisher import RabbitMQEventPublisher
from assignments.application.use_cases.reassign_ticket import ReassignTicket

repository = DjangoAssignmentRepository()
event_publisher = RabbitMQEventPublisher()

use_case = ReassignTicket(repository, event_publisher)
assignment = use_case.execute(
    ticket_id="TKT-003",
    new_priority="high"
)

print(f"Ticket reasignado a prioridad: {assignment.priority}")
```

### Buscar Asignación (Repository)

```python
from assignments.infrastructure.repository import DjangoAssignmentRepository

repository = DjangoAssignmentRepository()

# Por ticket_id
assignment = repository.find_by_ticket_id("TKT-001")
if assignment:
    print(f"Prioridad actual: {assignment.priority}")

# Por id
assignment = repository.find_by_id(1)

# Todas las asignaciones
all_assignments = repository.find_all()
for a in all_assignments:
    print(f"{a.ticket_id}: {a.priority}")
```

## Procesamiento de Eventos

### Evento Entrante: TicketCreated

Cuando el servicio de Tickets crea un nuevo ticket y emite el evento `ticket.created`:

```json
{
  "event_type": "ticket.created",
  "ticket_id": "TKT-004",
  "title": "Error en login",
  "description": "..."
}
```

El Assignment Service:

1. **Recibe** el evento vía RabbitMQ
2. **Procesa** en background con Celery
3. **Determina** prioridad automáticamente
4. **Crea** asignación usando `CreateAssignment` use case
5. **Emite** evento `assignment.created`

### Evento Saliente: AssignmentCreated

```json
{
  "event_type": "assignment.created",
  "assignment_id": 5,
  "ticket_id": "TKT-004",
  "priority": "high",
  "occurred_at": "2026-02-11T12:00:00Z"
}
```

## Validaciones de Dominio

### Prioridades Válidas

```python
# ✅ Válido
assignment = Assignment(
    ticket_id="TKT-001",
    priority="high",  # high, medium, low
    assigned_at=datetime.utcnow()
)

# ❌ Inválido - lanza ValueError
assignment = Assignment(
    ticket_id="TKT-001",
    priority="urgent",  # No es una prioridad válida
    assigned_at=datetime.utcnow()
)
```

### ticket_id Requerido

```python
# ❌ Inválido - lanza ValueError
assignment = Assignment(
    ticket_id="",  # Vacío no permitido
    priority="high",
    assigned_at=datetime.utcnow()
)
```

### Idempotencia

```python
# Primera vez: crea la asignación
use_case.execute(ticket_id="TKT-001", priority="high")

# Segunda vez: retorna la existente (no crea duplicado)
use_case.execute(ticket_id="TKT-001", priority="medium")
```

## Testing

### Test Unitario de Entity

```python
from datetime import datetime
from assignments.domain.entities import Assignment

def test_assignment_validates_priority():
    with pytest.raises(ValueError):
        Assignment(
            ticket_id="TKT-001",
            priority="invalid",
            assigned_at=datetime.utcnow()
        )

def test_assignment_change_priority():
    assignment = Assignment(
        ticket_id="TKT-001",
        priority="low",
        assigned_at=datetime.utcnow()
    )
    
    assignment.change_priority("high")
    assert assignment.priority == "high"
```

### Test de Use Case (con mock)

```python
from unittest.mock import Mock
from assignments.application.use_cases.create_assignment import CreateAssignment

def test_create_assignment_emits_event():
    mock_repo = Mock()
    mock_repo.find_by_ticket_id.return_value = None
    mock_repo.save.return_value = Assignment(
        id=1,
        ticket_id="TKT-001",
        priority="high",
        assigned_at=datetime.utcnow()
    )
    
    mock_publisher = Mock()
    
    use_case = CreateAssignment(mock_repo, mock_publisher)
    result = use_case.execute("TKT-001", "high")
    
    mock_publisher.publish.assert_called_once()
    assert result.ticket_id == "TKT-001"
```

## Configuración de RabbitMQ

Variables de entorno requeridas:

```bash
# En .env o docker-compose.yml
RABBITMQ_HOST=rabbitmq
RABBITMQ_EXCHANGE_NAME=ticket_events  # Exchange para recibir eventos
RABBITMQ_QUEUE_ASSIGNMENT=assignment_queue
RABBITMQ_EXCHANGE_ASSIGNMENT=assignment_events  # Exchange para emitir eventos
```

## Migraciones

```bash
# Crear migraciones (si es necesario)
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

## Iniciar Consumidor

```bash
# Iniciar el consumidor de RabbitMQ
python messaging/consumer.py
```

## Troubleshooting

### Error: "priority debe ser uno de ['high', 'medium', 'low']"

**Causa**: Se intentó usar una prioridad no válida.  
**Solución**: Usar solo: `high`, `medium`, `low`

### Error: "No existe asignación para el ticket"

**Causa**: Se intentó reasignar un ticket que no tiene asignación.  
**Solución**: Crear la asignación primero con `CreateAssignment`

### Eventos no se publican

**Causa**: RabbitMQ no está disponible o mal configurado.  
**Solución**: Verificar que RabbitMQ esté corriendo y las variables de entorno estén correctas.
