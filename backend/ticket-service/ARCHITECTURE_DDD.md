# Arquitectura DDD/EDA - Ticket Service

## Resumen

Este servicio ha sido refactorizado para aplicar **Domain-Driven Design (DDD)** y **Event-Driven Architecture (EDA)** siguiendo principios SOLID y arquitectura hexagonal (puertos y adaptadores).

## Estructura de Capas

```
tickets/
├── domain/                    # Capa de Dominio (independiente del framework)
│   ├── entities.py           # Entidad Ticket con reglas de negocio
│   ├── events.py             # Eventos de dominio (TicketCreated, TicketStatusChanged)
│   ├── exceptions.py         # Excepciones de dominio
│   ├── factories.py          # TicketFactory para creación válida
│   ├── repositories.py       # Interfaz TicketRepository (Puerto)
│   └── event_publisher.py    # Interfaz EventPublisher (Puerto)
│
├── application/               # Capa de Aplicación (casos de uso)
│   └── use_cases.py          # CreateTicketUseCase, ChangeTicketStatusUseCase
│
├── infrastructure/            # Capa de Infraestructura (adaptadores)
│   ├── repository.py         # DjangoTicketRepository (Adaptador Django ORM)
│   └── event_publisher.py    # RabbitMQEventPublisher (Adaptador RabbitMQ)
│
├── views.py                   # TicketViewSet refactorizado (thin controller)
├── serializer.py             # Serializer Django REST Framework (sin cambios)
└── models.py                 # Modelo Django para persistencia (sin cambios)
```

## Principios Aplicados

### 1. **Separation of Concerns**
- **Dominio**: Reglas de negocio puras, sin dependencias externas
- **Aplicación**: Orquestación de operaciones de dominio
- **Infraestructura**: Implementaciones técnicas (Django, RabbitMQ)
- **Presentación**: Controladores HTTP (ViewSets)

### 2. **Dependency Inversion Principle (DIP)**
- Los casos de uso dependen de abstracciones (`TicketRepository`, `EventPublisher`)
- Las implementaciones concretas dependen de las interfaces
- La dirección de dependencia apunta hacia el dominio

### 3. **Single Responsibility Principle (SRP)**
- `Ticket Entity`: Reglas de negocio y validaciones
- `TicketFactory`: Creación y validación de datos
- `Use Cases`: Orquestación de operaciones
- `Repository`: Abstracción de persistencia
- `ViewSet`: Traducción HTTP ↔ Dominio

## Reglas de Negocio Implementadas

### Creación de Tickets
- Un ticket siempre inicia en estado `OPEN`
- Título y descripción son obligatorios y no pueden estar vacíos
- Se genera un evento `TicketCreated` al persistir

### Cambio de Estado
- **No se puede cambiar el estado de un ticket `CLOSED`** → `TicketAlreadyClosed` exception
- Los cambios son **idempotentes**: si ya tiene ese estado, no hace nada
- Cada cambio válido genera un evento `TicketStatusChanged`
- Estados válidos: `OPEN`, `IN_PROGRESS`, `CLOSED`

## Flujo de Operaciones

### Crear Ticket

```
HTTP POST → ViewSet → CreateTicketUseCase → TicketFactory → Ticket Entity
                                          ↓
                                   DjangoRepository → Django ORM
                                          ↓
                                   EventPublisher → RabbitMQ
```

### Cambiar Estado

```
HTTP PATCH → ViewSet → ChangeTicketStatusUseCase → DjangoRepository (find)
                                                  ↓
                                            Ticket Entity (change_status)
                                                  ↓
                                            [Reglas de negocio aplicadas]
                                                  ↓
                                            DjangoRepository (save)
                                                  ↓
                                            EventPublisher → RabbitMQ
```

## Eventos de Dominio

### `TicketCreated`
```python
{
    "event_type": "ticket.created",
    "ticket_id": 123,
    "title": "...",
    "description": "...",
    "status": "OPEN",
    "occurred_at": "2024-01-01T10:00:00"
}
```

### `TicketStatusChanged`
```python
{
    "event_type": "ticket.status_changed",
    "ticket_id": 123,
    "old_status": "OPEN",
    "new_status": "IN_PROGRESS",
    "occurred_at": "2024-01-01T10:00:00"
}
```

## Ventajas de la Arquitectura

### 1. **Testabilidad**
- El dominio puede probarse sin Django ni RabbitMQ
- Los casos de uso pueden probarse con repositorios y publicadores mock
- Las capas están desacopladas

### 2. **Mantenibilidad**
- Lógica de negocio centralizada en el dominio
- Fácil de entender: cada capa tiene responsabilidades claras
- Los cambios en el framework no afectan el dominio

### 3. **Escalabilidad**
- Fácil cambiar Django ORM por otra implementación
- Fácil cambiar RabbitMQ por Kafka, SNS, etc.
- Los casos de uso son reutilizables (CLI, API, workers)

### 4. **Evolución**
- Nuevas reglas de negocio se agregan en el dominio
- Nuevos casos de uso se crean sin modificar existentes
- Eventos facilitan agregar funcionalidad sin acoplamiento

## Compatibilidad

✅ **Endpoints sin cambios**: Las URLs y contratos HTTP son idénticos  
✅ **Serializers sin cambios**: Compatible con DRF existente  
✅ **RabbitMQ funcional**: Los eventos se publican correctamente  
✅ **Sin dependencias nuevas**: Solo usa Django, DRF y pika

## Testing

### Pruebas de Dominio
```python
# Testar reglas de negocio sin framework
ticket = Ticket.create("Title", "Description")
assert ticket.status == Ticket.OPEN

ticket.change_status(Ticket.IN_PROGRESS)
assert ticket.status == Ticket.IN_PROGRESS

ticket.change_status(Ticket.CLOSED)
with pytest.raises(TicketAlreadyClosed):
    ticket.change_status(Ticket.OPEN)
```

### Pruebas de Casos de Uso
```python
# Usar mocks para repositorio y event publisher
mock_repo = Mock(spec=TicketRepository)
mock_publisher = Mock(spec=EventPublisher)

use_case = CreateTicketUseCase(mock_repo, mock_publisher)
command = CreateTicketCommand("Title", "Description")
ticket = use_case.execute(command)

mock_repo.save.assert_called_once()
mock_publisher.publish.assert_called_once()
```

## Migración desde Código Antiguo

### ⚠️ Componentes Deprecados

El refactor ha dejado obsoletos algunos componentes de la implementación anterior:

#### `tickets/messaging/events.py` - DEPRECADO
```python
# ❌ Implementación antigua (deprecada)
from tickets.messaging.events import publish_ticket_created
publish_ticket_created(ticket.id)

# ✅ Nueva implementación (usar esta)
from tickets.infrastructure.event_publisher import RabbitMQEventPublisher
from tickets.domain.events import TicketCreated

publisher = RabbitMQEventPublisher()
event = TicketCreated(
    occurred_at=datetime.now(),
    ticket_id=ticket.id,
    title=ticket.title,
    description=ticket.description,
    status=ticket.status
)
publisher.publish(event)
```

**Ver [COMPONENTS_TO_REMOVE.md](COMPONENTS_TO_REMOVE.md) para lista completa de componentes a eliminar.**

### Script de Verificación

Para encontrar usos de componentes deprecados:
```bash
python check_deprecated_usage.py
```

Este script identifica:
- Imports del módulo `messaging` obsoleto
- Llamadas a `publish_ticket_created()`
- Acceso directo al ORM en views
- Patrones de test obsoletos

## Próximos Pasos

1. **Unit Tests**: Crear pruebas para cada capa
2. **Integration Tests**: Probar casos de uso con BD real
3. **Event Sourcing**: Considerar almacenar todos los eventos
4. **CQRS**: Separar lecturas de escrituras si es necesario
5. **Saga Pattern**: Para transacciones distribuidas entre servicios

## Referencias

- **DDD**: Eric Evans - "Domain-Driven Design"
- **Hexagonal Architecture**: Alistair Cockburn
- **Clean Architecture**: Robert C. Martin
