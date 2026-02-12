# Guía Rápida: Trabajando con la Arquitectura DDD/EDA

## 🚀 Quick Start

### 1. Agregar una nueva regla de negocio

**Ejemplo**: "No se puede cerrar un ticket que no esté en progreso"

```python
# tickets/domain/entities.py

def change_status(self, new_status: str) -> None:
    # Validar estado actual
    if self.status == self.CLOSED:
        raise TicketAlreadyClosed(self.id)
    
    # ✅ NUEVA REGLA: Solo se puede cerrar si está en progreso
    if new_status == self.CLOSED and self.status != self.IN_PROGRESS:
        raise InvalidTicketStateTransition(self.status, new_status)
    
    # ... resto del código
```

**¿Dónde NO poner la regla?**
- ❌ En el ViewSet
- ❌ En el serializer
- ❌ En el Use Case
- ✅ En la entidad de dominio

---

### 2. Agregar un nuevo caso de uso

**Ejemplo**: "Asignar un ticket a un usuario"

#### Paso 1: Crear el comando

```python
# tickets/application/use_cases.py

@dataclass
class AssignTicketCommand:
    """Comando: Asignar un ticket a un usuario."""
    ticket_id: int
    user_id: int
```

#### Paso 2: Agregar método en la entidad (si aplica)

```python
# tickets/domain/entities.py

@dataclass
class Ticket:
    # ... campos existentes
    assigned_to: Optional[int] = None
    
    def assign_to(self, user_id: int) -> None:
        """Asigna el ticket a un usuario."""
        if self.status == self.CLOSED:
            raise TicketAlreadyClosed(self.id)
        
        self.assigned_to = user_id
        
        # Generar evento
        event = TicketAssigned(
            occurred_at=datetime.now(),
            ticket_id=self.id,
            user_id=user_id
        )
        self._domain_events.append(event)
```

#### Paso 3: Crear el caso de uso

```python
# tickets/application/use_cases.py

class AssignTicketUseCase:
    """Caso de uso: Asignar un ticket a un usuario."""
    
    def __init__(
        self,
        repository: TicketRepository,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, command: AssignTicketCommand) -> Ticket:
        # 1. Obtener ticket
        ticket = self.repository.find_by_id(command.ticket_id)
        
        if not ticket:
            raise ValueError(f"Ticket {command.ticket_id} no encontrado")
        
        # 2. Aplicar lógica de dominio
        ticket.assign_to(command.user_id)
        
        # 3. Persistir
        ticket = self.repository.save(ticket)
        
        # 4. Publicar eventos
        events = ticket.collect_domain_events()
        for event in events:
            self.event_publisher.publish(event)
        
        return ticket
```

#### Paso 4: Agregar endpoint en el ViewSet

```python
# tickets/views.py

class TicketViewSet(viewsets.ModelViewSet):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ... dependencias existentes
        
        # ✅ Agregar nuevo caso de uso
        self.assign_ticket_use_case = AssignTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
    
    @action(detail=True, methods=["post"], url_path="assign")
    def assign_ticket(self, request, pk=None):
        """Endpoint: POST /tickets/{id}/assign/"""
        user_id = request.data.get("user_id")
        
        if not user_id:
            return Response(
                {"error": "El campo 'user_id' es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            command = AssignTicketCommand(
                ticket_id=int(pk),
                user_id=int(user_id)
            )
            ticket = self.assign_ticket_use_case.execute(command)
            
            django_ticket = Ticket.objects.get(pk=ticket.id)
            return Response(
                TicketSerializer(django_ticket).data,
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
```

---

### 3. Agregar un nuevo tipo de evento

**Ejemplo**: "TicketAssigned"

#### Paso 1: Definir el evento

```python
# tickets/domain/events.py

@dataclass(frozen=True)
class TicketAssigned(DomainEvent):
    """Evento: Un ticket ha sido asignado a un usuario."""
    ticket_id: int
    user_id: int
```

#### Paso 2: Actualizar el traductor de eventos

```python
# tickets/infrastructure/event_publisher.py

def _translate_event(self, event: DomainEvent) -> Dict[str, Any]:
    if isinstance(event, TicketCreated):
        return { ... }
    elif isinstance(event, TicketStatusChanged):
        return { ... }
    elif isinstance(event, TicketAssigned):
        # ✅ Nueva traducción
        return {
            "event_type": "ticket.assigned",
            "ticket_id": event.ticket_id,
            "user_id": event.user_id,
            "occurred_at": event.occurred_at.isoformat()
        }
    else:
        return { ... }
```

---

### 4. Cambiar el adaptador de eventos (RabbitMQ → Kafka)

#### Paso 1: Crear nuevo adaptador

```python
# tickets/infrastructure/kafka_publisher.py

from kafka import KafkaProducer
from ..domain.event_publisher import EventPublisher
from ..domain.events import DomainEvent

class KafkaEventPublisher(EventPublisher):
    """Implementación del publicador usando Kafka."""
    
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092']
        )
    
    def publish(self, event: DomainEvent) -> None:
        message = self._translate_event(event)
        self.producer.send('tickets-topic', message)
    
    def _translate_event(self, event: DomainEvent) -> Dict[str, Any]:
        # Misma lógica que RabbitMQEventPublisher
        pass
```

#### Paso 2: Cambiar la inyección de dependencias

```python
# tickets/views.py

class TicketViewSet(viewsets.ModelViewSet):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.repository = DjangoTicketRepository()
        
        # ✅ Cambiar implementación (solo esta línea)
        # self.event_publisher = RabbitMQEventPublisher()
        self.event_publisher = KafkaEventPublisher()
        
        # Los casos de uso siguen igual
        self.create_ticket_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
```

**🎯 Resultado**: Cambiar RabbitMQ por Kafka sin tocar:
- ❌ Dominio (entidades, reglas de negocio)
- ❌ Casos de uso
- ❌ Repository
- ✅ Solo el adaptador de eventos

---

### 5. Usar los casos de uso fuera de Django REST

#### Desde un Management Command

```python
# tickets/management/commands/assign_urgent_tickets.py

from django.core.management.base import BaseCommand
from tickets.application.use_cases import (
    AssignTicketUseCase,
    AssignTicketCommand
)
from tickets.infrastructure.repository import DjangoTicketRepository
from tickets.infrastructure.event_publisher import RabbitMQEventPublisher


class Command(BaseCommand):
    help = 'Asigna tickets urgentes a usuarios disponibles'

    def handle(self, *args, **options):
        # ✅ Mismo caso de uso que en la API
        repository = DjangoTicketRepository()
        event_publisher = RabbitMQEventPublisher()
        
        use_case = AssignTicketUseCase(repository, event_publisher)
        
        # Lógica del comando
        urgent_tickets = repository.find_all()  # Filtrar urgentes
        for ticket in urgent_tickets:
            command = AssignTicketCommand(
                ticket_id=ticket.id,
                user_id=get_available_user()
            )
            use_case.execute(command)
            self.stdout.write(f'✅ Ticket {ticket.id} asignado')
```

#### Desde Celery Task

```python
# tickets/tasks.py

from celery import shared_task
from tickets.application.use_cases import (
    ChangeTicketStatusUseCase,
    ChangeTicketStatusCommand
)
from tickets.infrastructure.repository import DjangoTicketRepository
from tickets.infrastructure.event_publisher import RabbitMQEventPublisher


@shared_task
def auto_close_old_tickets():
    """Cierra automáticamente tickets antiguos."""
    
    # ✅ Reutilizar casos de uso
    repository = DjangoTicketRepository()
    event_publisher = RabbitMQEventPublisher()
    
    use_case = ChangeTicketStatusUseCase(repository, event_publisher)
    
    # Cerrar tickets antiguos
    old_tickets = find_old_tickets()  # Lógica de búsqueda
    for ticket in old_tickets:
        command = ChangeTicketStatusCommand(
            ticket_id=ticket.id,
            new_status="CLOSED"
        )
        use_case.execute(command)
```

---

## 📋 Checklist: ¿Dónde poner cada cosa?

### ✅ Entidad de Dominio (`domain/entities.py`)
- [ ] Reglas de negocio
- [ ] Validaciones de estado
- [ ] Transiciones de estado
- [ ] Generación de eventos de dominio
- [ ] Lógica que NO depende de servicios externos

### ✅ Caso de Uso (`application/use_cases.py`)
- [ ] Orquestación de operaciones
- [ ] Coordinación entre repositorio y event publisher
- [ ] Manejo de transacciones (si aplica)
- [ ] Lógica que depende de múltiples entidades

### ✅ Repository (`infrastructure/repository.py`)
- [ ] Persistencia en BD
- [ ] Traducción entre modelo Django ↔ entidad de dominio
- [ ] Queries complejas
- [ ] Caching (si aplica)

### ✅ Event Publisher (`infrastructure/event_publisher.py`)
- [ ] Traducción de eventos de dominio a mensajes
- [ ] Publicación en sistema de mensajería
- [ ] Manejo de errores de publicación

### ✅ ViewSet (`views.py`)
- [ ] Validación de entrada HTTP
- [ ] Traducción entre HTTP ↔ comandos
- [ ] Manejo de respuestas HTTP
- [ ] Traducción de excepciones de dominio a códigos HTTP

---

## 🎯 Reglas de Oro

### 1. **El dominio NO depende de nada**
```python
# ❌ MAL
from django.db import models
from rest_framework import serializers

class Ticket:
    # ...

# ✅ BIEN
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Ticket:
    # ...
```

### 2. **Los casos de uso dependen de abstracciones**
```python
# ❌ MAL
class CreateTicketUseCase:
    def __init__(self):
        self.repository = DjangoTicketRepository()  # Acoplamiento

# ✅ BIEN
class CreateTicketUseCase:
    def __init__(self, repository: TicketRepository):  # Abstracción
        self.repository = repository
```

### 3. **Las vistas solo traducen**
```python
# ❌ MAL
@action(detail=True, methods=["patch"])
def change_status(self, request, pk=None):
    ticket = Ticket.objects.get(pk=pk)
    ticket.status = request.data['status']
    ticket.save()

# ✅ BIEN
@action(detail=True, methods=["patch"])
def change_status(self, request, pk=None):
    command = ChangeTicketStatusCommand(...)
    ticket = self.use_case.execute(command)
    return Response(...)
```

### 4. **Los eventos son inmutables**
```python
# ❌ MAL
event = TicketCreated(...)
event.ticket_id = 999  # Mutar evento

# ✅ BIEN
@dataclass(frozen=True)  # Inmutable
class TicketCreated(DomainEvent):
    ticket_id: int
```

---

## 🧪 Testing

### Test de Dominio (Rápido, sin dependencias)
```python
def test_ticket_rules():
    ticket = Ticket.create("Title", "Description")
    assert ticket.status == Ticket.OPEN
    
    ticket.change_status(Ticket.CLOSED)
    with pytest.raises(TicketAlreadyClosed):
        ticket.change_status(Ticket.OPEN)
```

### Test de Caso de Uso (Con mocks)
```python
def test_use_case():
    mock_repo = Mock(spec=TicketRepository)
    mock_publisher = Mock(spec=EventPublisher)
    
    use_case = CreateTicketUseCase(mock_repo, mock_publisher)
    # ...
```

### Test de Integración (Con Django)
```python
class TestIntegration(TestCase):
    def test_full_workflow(self):
        # Usar implementaciones reales
        repository = DjangoTicketRepository()
        publisher = RabbitMQEventPublisher()
        # ...
```

---

## 📚 Recursos

- [ARCHITECTURE_DDD.md](ARCHITECTURE_DDD.md) - Documentación completa
- [BEFORE_AFTER.md](BEFORE_AFTER.md) - Comparación antes/después
- [examples.py](tickets/examples.py) - Ejemplos de uso
- [test_ddd.py](tickets/test_ddd.py) - Tests de ejemplo
