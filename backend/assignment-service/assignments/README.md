# Assignment Service - DDD Implementation

## Descripción

Servicio de asignación de tickets refactorizado con **Domain-Driven Design (DDD)** y **Event-Driven Architecture (EDA)**.

## Arquitectura

### Capas

```
📦 assignments/
├── 🔵 domain/           → Lógica de negocio pura (sin dependencias)
├── 🟢 application/      → Casos de uso y orquestación  
└── 🟡 infrastructure/   → Implementaciones (Django, RabbitMQ)
```

### Componentes Principales

| Capa | Componente | Responsabilidad |
|------|-----------|----------------|
| **Domain** | Assignment Entity | Reglas de negocio y validaciones |
| **Domain** | AssignmentRepository | Interface para persistencia |
| **Domain** | Domain Events | AssignmentCreated, AssignmentReassigned |
| **Application** | CreateAssignment | Caso de uso: crear asignación |
| **Application** | ReassignTicket | Caso de uso: reasignar ticket |
| **Application** | EventPublisher | Interface para publicar eventos |
| **Infrastructure** | DjangoAssignmentRepository | Implementación con Django ORM |
| **Infrastructure** | RabbitMQEventPublisher | Implementación con RabbitMQ |
| **Infrastructure** | TicketEventAdapter | Procesa eventos de Ticket |

## Instalación y Setup

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Aplicar Migraciones

```bash
python manage.py migrate
```

### 3. Verificar Arquitectura

```bash
python verify_ddd.py
```

**Salida esperada:**
```
✅ Estructura de carpetas correcta
✅ Todos los imports funcionan correctamente
✅ El dominio es independiente
✅ Todas las validaciones funcionan correctamente
🎉 La refactorización DDD está completa y funcional
```

### 4. Iniciar Servicios

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A assessment_service worker -l info

# Terminal 3: RabbitMQ consumer
python messaging/consumer.py
```

## Uso Rápido

### API REST

```bash
# Crear asignación
curl -X POST http://localhost:8000/assignments/ \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "TKT-001", "priority": "high"}'

# Listar asignaciones
curl http://localhost:8000/assignments/

# Reasignar ticket
curl -X POST http://localhost:8000/assignments/reassign/ \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "TKT-001", "priority": "low"}'
```

### Uso Programático

```python
from assignments.infrastructure.repository import DjangoAssignmentRepository
from assignments.infrastructure.messaging.event_publisher import RabbitMQEventPublisher
from assignments.application.use_cases.create_assignment import CreateAssignment

# Crear asignación
repository = DjangoAssignmentRepository()
event_publisher = RabbitMQEventPublisher()
use_case = CreateAssignment(repository, event_publisher)

assignment = use_case.execute(
    ticket_id="TKT-001",
    priority="high"
)
```

## Reglas de Negocio

1. ✅ **Un ticket solo puede tener una asignación activa**
2. ✅ **Prioridades válidas**: `high`, `medium`, `low`
3. ✅ **ticket_id es obligatorio y único**
4. ✅ **Operaciones idempotentes**
5. ✅ **Cada cambio emite un evento de dominio**

## Eventos

### Eventos Entrantes (Consume)

| Evento | Exchange | Queue | Acción |
|--------|----------|-------|--------|
| `ticket.created` | ticket_events | assignment_queue | Crea asignación automática |

### Eventos Salientes (Publica)

| Evento | Exchange | Datos |
|--------|----------|-------|
| `assignment.created` | assignment_events | assignment_id, ticket_id, priority |
| `assignment.reassigned` | assignment_events | assignment_id, old_priority, new_priority |

## Configuración

### Variables de Entorno

```bash
# Base de datos
DATABASE_NAME=assessment_db
DATABASE_USER=assessment_user
DATABASE_PASSWORD=assessment_pass
DATABASE_HOST=assessment-db

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_EXCHANGE_NAME=ticket_events
RABBITMQ_QUEUE_ASSIGNMENT=assignment_queue
RABBITMQ_EXCHANGE_ASSIGNMENT=assignment_events

# Django
ASSIGNMENT_SERVICE_SECRET_KEY=your-secret-key
DJANGO_DEBUG=true
```

## Testing

### Tests Unitarios (Dominio)

```bash
# Sin dependencias de Django
pytest assignments/domain/tests/
```

### Tests de Aplicación

```bash
# Con mocks
pytest assignments/application/tests/
```

### Tests de Integración

```bash
# Con Django
python manage.py test
```

## Estructura de Archivos

```
assignments/
├── domain/
│   ├── __init__.py
│   ├── entities.py              # Assignment entity
│   ├── repository.py            # Repository interface
│   └── events.py                # Domain events
│
├── application/
│   ├── __init__.py
│   ├── event_publisher.py       # Publisher interface
│   └── use_cases/
│       ├── __init__.py
│       ├── create_assignment.py
│       └── reassign_ticket.py
│
├── infrastructure/
│   ├── __init__.py
│   ├── django_models.py         # Django ORM model
│   ├── repository.py            # Django implementation
│   └── messaging/
│       ├── __init__.py
│       ├── event_publisher.py   # RabbitMQ implementation
│       └── event_adapter.py     # Event handler
│
├── models.py                     # Compatibility layer
├── serializers.py               # DRF serializers
├── views.py                     # DRF viewsets
├── urls.py                      # URL routes
├── tasks.py                     # Celery tasks
└── admin.py                     # Django admin
```

## Principios Aplicados

- ✅ **Single Responsibility Principle (SRP)**
- ✅ **Dependency Inversion Principle (DIP)**
- ✅ **Interface Segregation Principle (ISP)**
- ✅ **Domain Independence**
- ✅ **Event-Driven Architecture**

## Documentación Adicional

- 📖 [ARCHITECTURE_DDD.md](./ARCHITECTURE_DDD.md) - Arquitectura detallada
- 📖 [USAGE_GUIDE.md](./USAGE_GUIDE.md) - Guía de uso completa
- 📖 [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) - Resumen de refactorización

## Mantenimiento

### Agregar Nueva Regla de Negocio

1. Modificar `domain/entities.py`
2. Actualizar tests unitarios
3. Implementar en use case si es necesario

### Agregar Nuevo Caso de Uso

1. Crear archivo en `application/use_cases/`
2. Implementar lógica usando Repository y Entity
3. Emitir evento de dominio si aplica
4. Exponer en ViewSet si es necesario

### Agregar Nuevo Evento

1. Definir evento en `domain/events.py`
2. Emitir desde use case
3. Configurar consumer si es entrante
4. Actualizar adapter si es necesario

## Troubleshooting

| Problema | Solución |
|----------|----------|
| Error: "priority inválida" | Usar solo: high, medium, low |
| Error: "ticket_id vacío" | Proporcionar ticket_id válido |
| Eventos no se publican | Verificar RabbitMQ y variables de entorno |
| Imports no funcionan | Ejecutar `python verify_ddd.py` |

## Contributors

- Arquitectura: Senior Software Architect
- Implementación: DDD/EDA Expert

## License

Propietary

---

**Versión**: 2.0 (DDD Refactoring)  
**Última actualización**: Febrero 2026
