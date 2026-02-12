# Antes y Después de la Refactorización DDD

Este documento muestra la comparación lado a lado del código antes y después de aplicar DDD + EDA.

## 1. Marcar Notificación como Leída

### ❌ ANTES: Lógica en el ViewSet

```python
# api.py (ANTES)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-sent_at')
    serializer_class = NotificationSerializer

    @action(detail=True, methods=['patch'], url_path='read')
    def read(self, request, pk=None):
        notification = self.get_object()      # Acceso directo al ORM
        notification.read = True              # Lógica en el ViewSet
        notification.save(update_fields=['read'])
        return Response(status=status.HTTP_204_NO_CONTENT)
```

**Problemas:**
- ❌ Lógica de negocio mezclada con infraestructura HTTP
- ❌ Acoplamiento fuerte con Django ORM
- ❌ No hay eventos de dominio
- ❌ No hay validación de reglas de negocio
- ❌ Difícil de testear sin Django
- ❌ No se puede reutilizar la lógica fuera del ViewSet

### ✅ DESPUÉS: Arquitectura en Capas

#### Capa de Dominio (Reglas de Negocio)

```python
# domain/entities.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .events import DomainEvent, NotificationMarkedAsRead


@dataclass
class Notification:
    """Entidad de dominio con reglas de negocio encapsuladas."""
    
    id: Optional[int]
    ticket_id: str
    message: str
    sent_at: datetime
    read: bool = False
    
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)
    
    def mark_as_read(self) -> None:
        """
        Marca la notificación como leída aplicando reglas de negocio.
        
        Reglas:
        - Idempotente: si ya está leída, no hace nada
        - Genera evento de dominio en cada cambio válido
        """
        # Idempotencia: Si ya está leída, no hacer nada
        if self.read:
            return
        
        # Marcar como leída
        self.read = True
        
        # Generar evento de dominio
        event = NotificationMarkedAsRead(
            occurred_at=datetime.now(),
            notification_id=self.id,
            ticket_id=self.ticket_id
        )
        self._domain_events.append(event)
    
    def collect_domain_events(self) -> List[DomainEvent]:
        """Recolecta y limpia eventos para publicación."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
```

#### Capa de Aplicación (Casos de Uso)

```python
# application/use_cases.py
from dataclasses import dataclass

from ..domain.entities import Notification
from ..domain.repositories import NotificationRepository
from ..domain.event_publisher import EventPublisher
from ..domain.exceptions import NotificationNotFound


@dataclass
class MarkNotificationAsReadCommand:
    """Comando: Marcar una notificación como leída."""
    notification_id: int


class MarkNotificationAsReadUseCase:
    """
    Caso de uso: Marcar una notificación como leída.
    Orquesta dominio, persistencia y eventos.
    """
    
    def __init__(
        self,
        repository: NotificationRepository,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, command: MarkNotificationAsReadCommand) -> Notification:
        """Ejecuta el caso de uso."""
        # 1. Obtener la notificación
        notification = self.repository.find_by_id(command.notification_id)
        
        if not notification:
            raise NotificationNotFound(command.notification_id)
        
        # 2. Aplicar regla de negocio
        notification.mark_as_read()
        
        # 3. Persistir el cambio
        notification = self.repository.save(notification)
        
        # 4. Publicar eventos de dominio
        events = notification.collect_domain_events()
        for event in events:
            self.event_publisher.publish(event)
        
        return notification
```

#### Capa de Infraestructura (Adaptador Django)

```python
# infrastructure/repository.py
from typing import Optional, List

from ..domain.entities import Notification as DomainNotification
from ..domain.repositories import NotificationRepository
from ..models import Notification as DjangoNotification


class DjangoNotificationRepository(NotificationRepository):
    """Adaptador que traduce entre dominio y Django ORM."""
    
    def save(self, notification: DomainNotification) -> DomainNotification:
        """Persiste una notificación."""
        if notification.id:
            django_notification = DjangoNotification.objects.get(pk=notification.id)
            django_notification.read = notification.read
            django_notification.save(update_fields=['read'])
        else:
            django_notification = DjangoNotification.objects.create(
                ticket_id=notification.ticket_id,
                message=notification.message,
                read=notification.read
            )
            notification.id = django_notification.id
        
        return notification
    
    def find_by_id(self, notification_id: int) -> Optional[DomainNotification]:
        """Busca una notificación por ID."""
        try:
            django_notification = DjangoNotification.objects.get(pk=notification_id)
            return self._to_domain(django_notification)
        except DjangoNotification.DoesNotExist:
            return None
    
    def _to_domain(self, django_notification: DjangoNotification) -> DomainNotification:
        """Traduce modelo Django → entidad de dominio."""
        return DomainNotification(
            id=django_notification.id,
            ticket_id=django_notification.ticket_id,
            message=django_notification.message,
            sent_at=django_notification.sent_at,
            read=django_notification.read
        )
```

#### Capa de Presentación (Thin Controller)

```python
# api.py (DESPUÉS)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer
from .application.use_cases import (
    MarkNotificationAsReadUseCase,
    MarkNotificationAsReadCommand
)
from .infrastructure.repository import DjangoNotificationRepository
from .infrastructure.event_publisher import RabbitMQEventPublisher
from .domain.exceptions import NotificationNotFound, DomainException


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet refactorizado siguiendo DDD/EDA.
    Thin controller que delega a casos de uso.
    """
    
    queryset = Notification.objects.all().order_by('-sent_at')
    serializer_class = NotificationSerializer
    
    def __init__(self, *args, **kwargs):
        """Inyección de dependencias."""
        super().__init__(*args, **kwargs)
        
        self.repository = DjangoNotificationRepository()
        self.event_publisher = RabbitMQEventPublisher()
        
        self.mark_as_read_use_case = MarkNotificationAsReadUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )

    @action(detail=True, methods=['patch'], url_path='read')
    def read(self, request, pk=None):
        """Marca una notificación como leída."""
        try:
            # Crear comando
            command = MarkNotificationAsReadCommand(notification_id=int(pk))
            
            # Ejecutar caso de uso
            self.mark_as_read_use_case.execute(command)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except NotificationNotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except DomainException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

**Ventajas:**
- ✅ ViewSet como thin controller (solo HTTP)
- ✅ Lógica de negocio en entidad de dominio
- ✅ Eventos de dominio publicados automáticamente
- ✅ Testeable sin Django
- ✅ Código reutilizable
- ✅ Fácil de extender y mantener

## 2. Testing

### ❌ ANTES: Solo Tests de Integración

```python
# tests.py (ANTES)
from django.test import TestCase
from notifications.models import Notification


class NotificationTests(TestCase):
    def test_notification_model(self):
        n = Notification.objects.create(ticket_id='T-1', message='Hola')
        self.assertEqual(str(n).startswith('Notification for T-1'), True)
```

**Problemas:**
- ❌ Solo tests de integración (lentos)
- ❌ Requieren base de datos
- ❌ No prueban reglas de negocio
- ❌ Difícil identificar dónde falla

### ✅ DESPUÉS: Pirámide de Tests

#### Tests de Dominio (Rápidos, Sin Django)

```python
# tests/test_domain.py
import pytest
from datetime import datetime

from notifications.domain.entities import Notification
from notifications.domain.events import NotificationMarkedAsRead


class TestNotificationEntity:
    """Tests de reglas de negocio puras."""
    
    def test_mark_as_read_changes_state(self):
        """Marcar como leída cambia el estado y genera evento."""
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Ticket creado",
            sent_at=datetime.now(),
            read=False
        )
        
        notification.mark_as_read()
        
        assert notification.read is True
        events = notification.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], NotificationMarkedAsRead)
    
    def test_mark_as_read_is_idempotent(self):
        """Marcar como leída múltiples veces es idempotente."""
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Test",
            sent_at=datetime.now(),
            read=False
        )
        
        notification.mark_as_read()
        events = notification.collect_domain_events()
        assert len(events) == 1
        
        # Segunda vez: no genera evento
        notification.mark_as_read()
        events = notification.collect_domain_events()
        assert len(events) == 0
```

#### Tests de Casos de Uso (Con Mocks)

```python
# tests/test_use_cases.py
from unittest.mock import Mock
from datetime import datetime

from notifications.domain.entities import Notification
from notifications.application.use_cases import (
    MarkNotificationAsReadUseCase,
    MarkNotificationAsReadCommand
)


class TestMarkNotificationAsReadUseCase:
    def test_mark_as_read_success(self):
        """Ejecutar el caso de uso marca la notificación como leída."""
        # Mock del repositorio
        repository = Mock()
        event_publisher = Mock()
        
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Test",
            sent_at=datetime.now(),
            read=False
        )
        repository.find_by_id.return_value = notification
        repository.save.return_value = notification
        
        use_case = MarkNotificationAsReadUseCase(repository, event_publisher)
        command = MarkNotificationAsReadCommand(notification_id=1)
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.read is True
        repository.save.assert_called_once()
        event_publisher.publish.assert_called_once()
```

## 3. Estructura de Archivos

### ❌ ANTES: Código Monolítico

```
notifications/
├── models.py          # Modelo + Lógica de negocio mezclada
├── api.py             # ViewSet con lógica de negocio
├── serializers.py     # Serializers
├── tests.py           # Tests de integración solamente
└── urls.py            # Rutas
```

### ✅ DESPUÉS: Arquitectura en Capas

```
notifications/
├── domain/                    # ← Capa de dominio (núcleo)
│   ├── __init__.py
│   ├── entities.py           # Entidades con reglas de negocio
│   ├── events.py             # Eventos de dominio
│   ├── repositories.py       # Interfaces (puertos)
│   ├── event_publisher.py    # Interface (puerto)
│   └── exceptions.py         # Excepciones de dominio
│
├── application/              # ← Capa de aplicación
│   ├── __init__.py
│   └── use_cases.py          # Casos de uso (orquestación)
│
├── infrastructure/           # ← Capa de infraestructura
│   ├── __init__.py
│   ├── repository.py         # Implementación Django
│   └── event_publisher.py    # Implementación RabbitMQ
│
├── tests/                    # ← Tests organizados
│   ├── __init__.py
│   ├── test_domain.py        # Tests de dominio (rápidos)
│   ├── test_use_cases.py     # Tests de casos de uso (mocks)
│   ├── test_infrastructure.py # Tests de repositorio
│   ├── test_views.py         # Tests de ViewSet
│   ├── test_integration.py   # Tests de integración
│   └── README.md             # Guía de testing
│
├── models.py                 # Solo modelo Django (persistencia)
├── serializers.py            # Sin cambios
├── api.py                    # ViewSet refactorizado (thin)
└── urls.py                   # Sin cambios
```

## 4. Flujo de Ejecución

### ❌ ANTES: Flujo Acoplado

```
HTTP Request
    ↓
ViewSet.read()
    ├─ notification = self.get_object()  # ORM
    ├─ notification.read = True          # Sin validación
    ├─ notification.save()               # Sin eventos
    └─ return Response(204)
```

### ✅ DESPUÉS: Flujo Limpio

```
HTTP Request
    ↓
ViewSet.read() [Thin Controller]
    ↓
MarkNotificationAsReadCommand
    ↓
MarkNotificationAsReadUseCase.execute() [Orchestrator]
    ├─→ repository.find_by_id()
    │       ↓
    │   DjangoNotificationRepository [Adapter]
    │       ↓
    │   Django ORM
    │
    ├─→ notification.mark_as_read() [Domain Logic]
    │       ├─ Validar estado
    │       ├─ Cambiar estado
    │       └─ Generar evento
    │
    ├─→ repository.save()
    │       ↓
    │   Django ORM
    │
    └─→ event_publisher.publish()
            ↓
        RabbitMQEventPublisher [Adapter]
            ↓
        RabbitMQ
    ↓
HTTP Response 204
```

## Resumen de Mejoras

| Aspecto              | ❌ Antes                          | ✅ Después                       |
|----------------------|-----------------------------------|----------------------------------|
| **Lógica de Negocio** | En ViewSet                        | En entidad de dominio            |
| **Acoplamiento**      | Fuerte con Django ORM             | Abstraído con repository         |
| **Eventos**           | No hay                            | Domain events automáticos        |
| **Testabilidad**      | Solo tests con DB (lentos)        | Tests unitarios rápidos          |
| **Reutilización**     | Lógica atada al ViewSet           | Casos de uso reutilizables       |
| **Validación**        | Sin validación de reglas          | Reglas encapsuladas              |
| **Extensibilidad**    | Difícil agregar comportamiento    | Fácil agregar casos de uso       |
| **Mantenibilidad**    | Código disperso                   | Responsabilidades claras         |
| **Idempotencia**      | No garantizada                    | Implementada en el dominio       |
| **Principios SOLID**  | Violados                          | Aplicados correctamente          |

## Compatibilidad

### ✅ Sin Cambios en API

- **Endpoints:** Sin cambios
- **Serializers:** Sin cambios
- **URLs:** Sin cambios
- **Respuestas HTTP:** Sin cambios
- **Contratos:** 100% compatibles

### ✅ Funcionalidad Mejorada

- Idempotencia garantizada
- Eventos de dominio
- Validación de reglas de negocio
- Mejor manejo de errores
- Arquitectura extensible

---

**Conclusión:** La refactorización ha transformado código monolítico en una arquitectura limpia, mantenible y testeable, sin romper compatibilidad con el sistema existente.
