# Arquitectura DDD - Assignment Service

## Estructura del Módulo

El módulo **Assignment** ha sido refactorizado aplicando Domain-Driven Design (DDD) y Event-Driven Architecture (EDA) de forma pragmática.

### Capas

```
assignments/
├── domain/                          # Capa de Dominio (sin dependencias externas)
│   ├── entities.py                 # Assignment entity con reglas de negocio
│   ├── repository.py               # AssignmentRepository interface (puerto)
│   └── events.py                   # Domain Events (AssignmentCreated, AssignmentReassigned)
│
├── application/                     # Capa de Aplicación (orquestación)
│   ├── event_publisher.py          # EventPublisher interface (puerto)
│   └── use_cases/
│       ├── create_assignment.py    # Caso de uso: crear asignación
│       └── reassign_ticket.py      # Caso de uso: reasignar ticket
│
├── infrastructure/                  # Capa de Infraestructura (implementaciones)
│   ├── django_models.py            # TicketAssignmentModel (ORM)
│   ├── repository.py               # DjangoAssignmentRepository (implementación)
│   └── messaging/
│       ├── event_publisher.py      # RabbitMQEventPublisher (implementación)
│       ├── event_adapter.py        # TicketEventAdapter (transforma eventos)
│       └── consumer.py             # (movido desde messaging/ raíz)
│
├── models.py                        # Importa desde infrastructure (compatibilidad Django)
├── serializers.py                  # DRF serializers (sin cambios)
├── views.py                        # ViewSet refactorizado (usa casos de uso)
├── urls.py                         # URLs (sin cambios)
├── tasks.py                        # Celery tasks (refactorizado)
└── admin.py                        # Django admin (sin cambios)
```

## Principios Aplicados

### 1. Separación de Capas

- **Dominio**: Entidades y reglas de negocio puras. No conoce Django, DRF ni RabbitMQ.
- **Aplicación**: Casos de uso que orquestan el dominio. Define puertos (interfaces).
- **Infraestructura**: Implementaciones concretas (Django ORM, RabbitMQ, etc.).

### 2. Inversión de Dependencias (DIP)

```
Views → Use Cases → Repository Interface
                         ↑
                    Django Repository
```

El dominio depende de abstracciones, no de implementaciones concretas.

### 3. Responsabilidad Única (SRP)

- **Entity**: Contiene reglas de negocio y validaciones
- **Repository**: Solo persistencia
- **Use Case**: Solo orquestación de una operación
- **ViewSet**: Solo exposición HTTP
- **Adapter**: Solo traducción de eventos

## Flujos Principales

### Flujo 1: Crear Assignment vía API

```
1. Cliente → POST /assignments/ {ticket_id, priority}
2. ViewSet valida con serializer
3. ViewSet ejecuta CreateAssignment use case
4. Use case crea Assignment entity (valida reglas)
5. Use case persiste via DjangoAssignmentRepository
6. Use case emite AssignmentCreated event via RabbitMQEventPublisher
7. ViewSet retorna respuesta HTTP
```

### Flujo 2: Procesar Evento TicketCreated

```
1. RabbitMQ recibe evento TicketCreated
2. Consumer recibe mensaje → delega a Celery
3. Celery task → invoca handle_ticket_event
4. Handler → usa TicketEventAdapter
5. Adapter → determina prioridad y ejecuta CreateAssignment use case
6. Use case crea Assignment y emite evento
```

### Flujo 3: Reasignar Ticket

```
1. Cliente → POST /assignments/reassign/ {ticket_id, priority}
2. ViewSet ejecuta ReassignTicket use case
3. Use case busca Assignment existente
4. Use case cambia prioridad (valida en entity)
5. Use case persiste cambios
6. Use case emite AssignmentReassigned event
7. ViewSet retorna respuesta HTTP
```

## Reglas de Dominio

1. **Un ticket solo puede tener una asignación activa** → `CreateAssignment` es idempotente
2. **La prioridad debe ser válida** → Validado en `Assignment` entity
3. **Cada cambio válido genera un evento** → Use cases emiten eventos
4. **ticket_id es requerido** → Validado en `Assignment` entity

## Eventos de Dominio

### AssignmentCreated
```python
{
    "event_type": "assignment.created",
    "assignment_id": 123,
    "ticket_id": "TKT-001",
    "priority": "high",
    "occurred_at": "2026-02-11T10:30:00Z"
}
```

### AssignmentReassigned
```python
{
    "event_type": "assignment.reassigned", 
    "assignment_id": 123,
    "ticket_id": "TKT-001",
    "old_priority": "low",
    "new_priority": "high",
    "occurred_at": "2026-02-11T11:00:00Z"
}
```

## Compatibilidad

✅ Endpoints y URLs sin cambios  
✅ Serializers sin cambios  
✅ Contratos HTTP sin cambios  
✅ Django Admin funcional  
✅ Migraciones compatibles (mismo db_table)  

## Ventajas de la Nueva Arquitectura

1. **Testeable**: Dominio puro, fácil de testear sin Django
2. **Mantenible**: Responsabilidades claras en cada capa
3. **Extensible**: Fácil agregar nuevas reglas o casos de uso
4. **Desacoplado**: Dominio independiente de infraestructura
5. **Trazable**: Eventos permiten auditoría completa

## Próximos Pasos (Opcionales)

- [ ] Actualizar tests unitarios para el dominio
- [ ] Agregar tests de integración para use cases
- [ ] Implementar análisis de prioridad más sofisticado
- [ ] Agregar métricas y observabilidad
