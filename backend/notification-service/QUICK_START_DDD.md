# Quick Start - Notification Service DDD

## Estructura Rápida

```
notifications/
├── domain/           → Reglas de negocio puras
├── application/      → Casos de uso
├── infrastructure/   → Adaptadores (Django, RabbitMQ)
└── tests/            → Tests por capa
```

## Flujo: Marcar Notificación como Leída

### 1. ViewSet (Thin Controller)

```python
# api.py
@action(detail=True, methods=['patch'], url_path='read')
def read(self, request, pk=None):
    command = MarkNotificationAsReadCommand(notification_id=int(pk))
    self.mark_as_read_use_case.execute(command)
    return Response(status=status.HTTP_204_NO_CONTENT)
```

### 2. Caso de Uso (Orquestación)

```python
# application/use_cases.py
def execute(self, command: MarkNotificationAsReadCommand) -> Notification:
    notification = self.repository.find_by_id(command.notification_id)
    notification.mark_as_read()  # ← Regla de negocio
    notification = self.repository.save(notification)
    
    for event in notification.collect_domain_events():
        self.event_publisher.publish(event)  # ← EDA
    
    return notification
```

### 3. Entidad de Dominio (Reglas)

```python
# domain/entities.py
def mark_as_read(self) -> None:
    if self.read:
        return  # Idempotente
    
    self.read = True
    self._domain_events.append(NotificationMarkedAsRead(...))
```

## Agregar Nuevo Caso de Uso

### Paso 1: Definir Comando

```python
# application/use_cases.py
@dataclass
class GetUnreadNotificationsCommand:
    user_id: int
```

### Paso 2: Implementar Caso de Uso

```python
class GetUnreadNotificationsUseCase:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository
    
    def execute(self, command: GetUnreadNotificationsCommand) -> List[Notification]:
        return self.repository.find_unread_by_user(command.user_id)
```

### Paso 3: Agregar Método al Repository

```python
# domain/repositories.py (interfaz)
@abstractmethod
def find_unread_by_user(self, user_id: int) -> List[Notification]:
    pass

# infrastructure/repository.py (implementación)
def find_unread_by_user(self, user_id: int) -> List[Notification]:
    django_notifs = DjangoNotification.objects.filter(
        user_id=user_id, 
        read=False
    )
    return [self._to_domain(n) for n in django_notifs]
```

### Paso 4: Usar en ViewSet

```python
# api.py
@action(detail=False, methods=['get'])
def unread(self, request):
    command = GetUnreadNotificationsCommand(user_id=request.user.id)
    notifications = self.get_unread_use_case.execute(command)
    
    # Convertir a modelos Django para serialización
    django_models = [self.repository.to_django_model(n) for n in notifications]
    return Response(NotificationSerializer(django_models, many=True).data)
```

## Testing

```bash
# Tests de dominio (rápidos, sin DB)
python manage.py test notifications.tests.test_domain

# Tests de casos de uso (con mocks)
python manage.py test notifications.tests.test_use_cases

# Tests de integración (lentos, con DB)
python manage.py test notifications.tests.test_infrastructure
```

## Patrón de Inyección de Dependencias

```python
# ViewSet.__init__()
self.repository = DjangoNotificationRepository()
self.event_publisher = RabbitMQEventPublisher()

self.mark_as_read_use_case = MarkNotificationAsReadUseCase(
    repository=self.repository,
    event_publisher=self.event_publisher
)
```

## Manejo de Excepciones de Dominio

```python
try:
    self.use_case.execute(command)
except NotificationNotFound as e:
    return Response({"error": str(e)}, status=404)
except DomainException as e:
    return Response({"error": str(e)}, status=400)
```

## Principios Clave

1. **Dominio NO conoce Django** → Reglas de negocio puras
2. **ViewSet delega** → No contiene lógica de negocio
3. **Repository traduce** → Entidad ↔ Modelo Django
4. **Eventos automáticos** → `collect_domain_events()`
5. **Idempotencia** → Verificar estado antes de cambiar

## Cheatsheet

| Necesito...                  | Voy a...                          | Archivo                    |
|------------------------------|-----------------------------------|----------------------------|
| Agregar regla de negocio     | Método en entidad                 | `domain/entities.py`       |
| Nuevo evento                 | Dataclass frozen                  | `domain/events.py`         |
| Nuevo caso de uso            | UseCase + Command                 | `application/use_cases.py` |
| Consulta específica          | Método en repository              | `infrastructure/repository.py` |
| Endpoint HTTP                | Action en ViewSet                 | `api.py`                   |
| Test sin DB                  | Test de dominio                   | `tests/test_domain.py`     |

## Ver Más

- `ARCHITECTURE_DDD.md` - Documentación completa
- `tests/README.md` - Guía de testing
