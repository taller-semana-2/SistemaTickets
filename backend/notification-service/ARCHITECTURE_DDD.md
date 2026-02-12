# Arquitectura DDD + EDA - Notification Service

## Visión General

Este documento describe la refactorización del módulo `notification-service` aplicando **Domain-Driven Design (DDD)** y **Event-Driven Architecture (EDA)** de forma ligera y pragmática.

## Objetivo de la Refactorización

Separar el dominio de notificaciones del framework Django, aplicando únicamente los patrones que aportan valor real:

- ✅ **Entity** - Encapsular reglas de negocio
- ✅ **Repository** - Abstraer la persistencia
- ✅ **Use Case** - Orquestar operaciones de dominio
- ✅ **Domain Events** - Comunicar cambios importantes
- ✅ **Adapter** - Traducir entre capas

## Estructura del Proyecto

```
notifications/
├── domain/                    # Capa de dominio (núcleo del negocio)
│   ├── entities.py           # Entidad Notification con reglas de negocio
│   ├── events.py             # Eventos de dominio (NotificationMarkedAsRead)
│   ├── repositories.py       # Interfaz NotificationRepository (puerto)
│   ├── event_publisher.py    # Interfaz EventPublisher (puerto)
│   └── exceptions.py         # Excepciones de dominio
│
├── application/              # Capa de aplicación (casos de uso)
│   └── use_cases.py          # MarkNotificationAsReadUseCase
│
├── infrastructure/           # Capa de infraestructura (adaptadores)
│   ├── repository.py         # DjangoNotificationRepository (implementación)
│   └── event_publisher.py    # RabbitMQEventPublisher (implementación)
│
├── tests/                    # Tests organizados por capa
│   ├── test_domain.py        # Tests de entidades y reglas de negocio
│   ├── test_use_cases.py     # Tests de casos de uso
│   ├── test_infrastructure.py # Tests del repositorio Django
│   ├── test_views.py         # Tests del ViewSet
│   └── test_integration.py   # Tests de integración
│
├── models.py                 # Modelo Django (solo persistencia)
├── serializers.py            # Serializers DRF (sin cambios)
├── api.py                    # ViewSet refactorizado (thin controller)
└── urls.py                   # Rutas (sin cambios)
```

## Capas y Responsabilidades

### 1. Dominio (`domain/`)

**Responsabilidad:** Contiene las reglas de negocio puras, independientes de Django.

#### `entities.py` - Entidad Notification

```python
@dataclass
class Notification:
    id: Optional[int]
    ticket_id: str
    message: str
    sent_at: datetime
    read: bool = False
    
    def mark_as_read(self) -> None:
        """Regla de negocio: marcar como leída (idempotente)."""
        if self.read:
            return  # Idempotencia
        
        self.read = True
        self._domain_events.append(NotificationMarkedAsRead(...))
```

**Reglas implementadas:**
- ✅ Una notificación puede marcarse como leída solo una vez
- ✅ Marcar como leída es idempotente (no genera evento si ya está leída)
- ✅ Cada cambio válido genera un evento de dominio

#### `events.py` - Eventos de Dominio

```python
@dataclass(frozen=True)
class NotificationMarkedAsRead(DomainEvent):
    """Evento: Una notificación fue marcada como leída."""
    notification_id: int
    ticket_id: str
```

**Características:**
- Inmutables (`frozen=True`)
- Representan hechos que ya ocurrieron
- Comunicación asíncrona entre módulos

#### `repositories.py` - Interfaz Repository

```python
class NotificationRepository(ABC):
    @abstractmethod
    def save(self, notification: Notification) -> Notification:
        pass
    
    @abstractmethod
    def find_by_id(self, notification_id: int) -> Optional[Notification]:
        pass
```

**Principio aplicado:** Dependency Inversion Principle (DIP)
- El dominio define QUÉ necesita, no CÓMO se implementa
- La infraestructura implementa el contrato

### 2. Aplicación (`application/`)

**Responsabilidad:** Orquesta operaciones de dominio.

#### `use_cases.py` - Caso de Uso

```python
class MarkNotificationAsReadUseCase:
    def __init__(self, repository: NotificationRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, command: MarkNotificationAsReadCommand) -> Notification:
        # 1. Obtener notificación
        notification = self.repository.find_by_id(command.notification_id)
        
        # 2. Aplicar regla de negocio
        notification.mark_as_read()
        
        # 3. Persistir
        notification = self.repository.save(notification)
        
        # 4. Publicar eventos
        for event in notification.collect_domain_events():
            self.event_publisher.publish(event)
        
        return notification
```

**Responsabilidades:**
1. Validar existencia de la entidad
2. Ejecutar lógica de dominio
3. Coordinar persistencia
4. Publicar eventos

### 3. Infraestructura (`infrastructure/`)

**Responsabilidad:** Implementar contratos definidos por el dominio.

#### `repository.py` - Repositorio Django

```python
class DjangoNotificationRepository(NotificationRepository):
    def save(self, notification: DomainNotification) -> DomainNotification:
        # Traducir entidad de dominio → modelo Django
        if notification.id:
            django_notif = DjangoNotification.objects.get(pk=notification.id)
            django_notif.read = notification.read
            django_notif.save(update_fields=['read'])
        else:
            django_notif = DjangoNotification.objects.create(...)
        
        return notification
    
    def _to_domain(self, django_notif) -> DomainNotification:
        # Traducir modelo Django → entidad de dominio
        return DomainNotification(...)
```

**Patrón:** Adapter Pattern
- Traduce entre modelo Django y entidad de dominio
- Aísla el dominio de la tecnología de persistencia

#### `event_publisher.py` - Publicador RabbitMQ

```python
class RabbitMQEventPublisher(EventPublisher):
    def publish(self, event: DomainEvent) -> None:
        message = self._translate_event(event)
        self._publish_to_rabbitmq(message)
```

**Responsabilidades:**
- Traducir eventos de dominio a mensajes RabbitMQ
- Gestionar conexión y publicación

### 4. Presentación (`api.py`)

**Responsabilidad:** Thin Controller que delega a casos de uso.

```python
class NotificationViewSet(viewsets.ModelViewSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Inyección de dependencias
        self.repository = DjangoNotificationRepository()
        self.event_publisher = RabbitMQEventPublisher()
        self.mark_as_read_use_case = MarkNotificationAsReadUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
    
    @action(detail=True, methods=['patch'], url_path='read')
    def read(self, request, pk=None):
        try:
            command = MarkNotificationAsReadCommand(notification_id=int(pk))
            self.mark_as_read_use_case.execute(command)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotificationNotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
```

**NO responsable de:**
- ❌ Lógica de negocio
- ❌ Acceso directo al ORM
- ❌ Publicación de eventos

**Responsable de:**
- ✅ Validación HTTP
- ✅ Ejecutar casos de uso
- ✅ Traducir excepciones a respuestas HTTP

## Flujo de Ejecución

### Marcar Notificación como Leída

```
HTTP PATCH /api/notifications/1/read/
    ↓
NotificationViewSet.read()
    ↓
MarkNotificationAsReadCommand(notification_id=1)
    ↓
MarkNotificationAsReadUseCase.execute()
    ├─→ repository.find_by_id(1) → DomainNotification
    ├─→ notification.mark_as_read() → genera evento
    ├─→ repository.save(notification) → persiste en DB
    └─→ event_publisher.publish(event) → RabbitMQ
    ↓
HTTP 204 No Content
```

## Beneficios de la Arquitectura

### 1. Separación de Responsabilidades (SRP)
- Cada clase tiene una única razón para cambiar
- Dominio NO conoce Django, DRF ni RabbitMQ

### 2. Testabilidad
- Tests de dominio: sin Django (rápidos, puros)
- Tests de casos de uso: con mocks (sin DB)
- Tests de infraestructura: con Django (integración)

### 3. Inversión de Dependencias (DIP)
- El dominio define interfaces
- La infraestructura las implementa
- Fácil cambiar de Django ORM a otro sistema

### 4. Extensibilidad
- Agregar nuevos casos de uso sin tocar el dominio
- Cambiar de RabbitMQ a Kafka modificando solo el adaptador

### 5. Mantenibilidad
- Código más legible y autodocumentado
- Reglas de negocio centralizadas en entidades
- Cambios aislados por capa

## Reglas de Negocio Implementadas

### Idempotencia
```python
def mark_as_read(self):
    if self.read:
        return  # No hace nada si ya está leída
    # ...
```

### Eventos Solo en Cambios Válidos
```python
def mark_as_read(self):
    if self.read:
        return  # No genera evento
    
    self.read = True
    self._domain_events.append(NotificationMarkedAsRead(...))  # Evento generado
```

## Comparación: Antes vs Después

### ❌ Antes (Código Monolítico)

```python
class NotificationViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        notification = self.get_object()  # Acceso directo al ORM
        notification.read = True          # Lógica en el ViewSet
        notification.save()               # Sin eventos
        return Response(status=204)
```

**Problemas:**
- ❌ Lógica de negocio en el ViewSet
- ❌ Acoplamiento fuerte con Django ORM
- ❌ No hay eventos de dominio
- ❌ Difícil de testear sin Django

### ✅ Después (DDD + EDA)

```python
class NotificationViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        command = MarkNotificationAsReadCommand(notification_id=int(pk))
        self.mark_as_read_use_case.execute(command)  # Delega al caso de uso
        return Response(status=204)
```

**Ventajas:**
- ✅ ViewSet como thin controller
- ✅ Lógica en entidad de dominio
- ✅ Eventos publicados automáticamente
- ✅ Testeable sin Django

## Compatibilidad

### ✅ Sin Cambios en Contratos HTTP

- Endpoints: sin cambios
- Serializers: sin cambios
- URLs: sin cambios
- Respuestas HTTP: sin cambios

### ✅ Funcionalidad Completa

- CRUD completo de notificaciones
- Marcar como leída (idempotente)
- Eventos de dominio publicados
- Integración con RabbitMQ

## Testing

### Pirámide de Tests

```
        ╱╲
       ╱ E2E╲              test_integration.py (pocos, lentos)
      ╱──────╲
     ╱   API  ╲            test_views.py (algunos)
    ╱──────────╲
   ╱ Use Cases  ╲          test_use_cases.py (varios)
  ╱──────────────╲
 ╱ Domain + Infra ╲        test_domain.py + test_infrastructure.py
╱──────────────────╲       (muchos, rápidos)
```

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test notifications.tests

# Por capa
python manage.py test notifications.tests.test_domain
python manage.py test notifications.tests.test_use_cases
python manage.py test notifications.tests.test_infrastructure
```

## Próximos Pasos

### Opcional: Agregar Más Casos de Uso

- `CreateNotificationUseCase` - Si la creación requiere lógica compleja
- `GetUnreadNotificationsUseCase` - Para queries específicas

### Opcional: Value Objects

Si la lógica de `ticket_id` se vuelve compleja, extraer a Value Object:

```python
@dataclass(frozen=True)
class TicketId:
    value: str
    
    def __post_init__(self):
        if not self.value.startswith('T-'):
            raise ValueError("Invalid ticket ID format")
```

## Conclusión

Esta refactorización ha logrado:

1. ✅ Separar dominio del framework Django
2. ✅ Implementar reglas de negocio claras e idempotentes
3. ✅ Emitir eventos de dominio para EDA
4. ✅ Mantener compatibilidad 100% con APIs existentes
5. ✅ Mejorar testabilidad y mantenibilidad

**Arquitectura ligera, pragmática y mantenible.**
