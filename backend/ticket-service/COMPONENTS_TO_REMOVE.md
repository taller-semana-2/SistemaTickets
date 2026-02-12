# Componentes a Eliminar/Deprecar - Refactorización DDD/EDA

## 🗑️ Componentes que DEBEN Eliminarse/Deprecarse

Tras la refactorización a DDD/EDA, los siguientes componentes del diseño antiguo están **obsoletos** y deben migrarse o eliminarse:

---

## 1. ❌ `tickets/messaging/` (Directorio completo)

### ¿Por qué eliminarlo?
Este directorio contenía la implementación antigua de publicación de eventos, **acoplada directamente a RabbitMQ y sin abstracción**.

### Archivos obsoletos:

#### `tickets/messaging/events.py`
```python
# ❌ OBSOLETO - Reemplazado por RabbitMQEventPublisher
def publish_ticket_created(ticket_id):
    """Publica un evento ticket.created en RabbitMQ usando exchange fanout"""
    connection = pika.BlockingConnection(...)
    # Código acoplado directamente a pika
```

**Problemas:**
- ❌ Acoplamiento directo a RabbitMQ (sin abstracción)
- ❌ Solo publica `ticket.created` (no otros eventos)
- ❌ Recibe solo `ticket_id` (datos incompletos)
- ❌ No sigue el patrón Domain Events
- ❌ Difícil de testear (requiere RabbitMQ real)
- ❌ No se puede cambiar a otro broker sin modificar código

**Reemplazado por:**
```python
# ✅ NUEVO - infrastructure/event_publisher.py
class RabbitMQEventPublisher(EventPublisher):
    """Implementación desacoplada, testeable y extensible."""
    
    def publish(self, event: DomainEvent) -> None:
        # Soporta cualquier tipo de evento de dominio
        # Traducible a diferentes formatos
        # Fácil de mockear en tests
```

#### `tickets/messaging/rabbitmq.py`
```python
# ❌ Archivo vacío - Sin propósito
```

**Acción:** Eliminar completamente.

#### `tickets/messaging/__init__.py`
```python
# ❌ Archivo vacío
```

**Acción:** Eliminar junto con el directorio.

---

## 2. ⚠️ Tests Antiguos que Prueban Implementación Obsoleta

### `tickets/tests.py` - Tests a Actualizar

#### Test obsoleto 1:
```python
# ❌ OBSOLETO - Prueba la implementación antigua
def test_perform_create_calls_publish(self):
    with patch('tickets.views.publish_ticket_created') as mock_pub:
        view.perform_create(s)
        self.assertTrue(mock_pub.called)
```

**Problema:** 
- Prueba que `publish_ticket_created` se llama desde el ViewSet
- El ViewSet ya no llama a esta función (usa casos de uso)

**Reemplazo sugerido:**
```python
# ✅ NUEVO - Prueba que el caso de uso se ejecuta
def test_perform_create_executes_use_case(self):
    with patch.object(view.create_ticket_use_case, 'execute') as mock_uc:
        view.perform_create(s)
        mock_uc.assert_called_once()
```

#### Test obsoleto 2:
```python
# ❌ OBSOLETO
def test_publish_ticket_created_raises_when_pika_fails(self):
    with patch('tickets.messaging.events.pika.BlockingConnection', ...):
        messaging.events.publish_ticket_created(12345)
```

**Problema:**
- Prueba la función antigua de publicación
- Ya no se usa en producción

**Reemplazo sugerido:**
```python
# ✅ NUEVO - Prueba el adaptador
def test_rabbitmq_publisher_handles_connection_errors(self):
    publisher = RabbitMQEventPublisher()
    with patch('pika.BlockingConnection', side_effect=Exception('conn fail')):
        with pytest.raises(Exception):
            publisher.publish(TicketCreated(...))
```

### `tickets/test_integration.py` - Tests a Actualizar

```python
# ❌ OBSOLETO
from .messaging.events import publish_ticket_created

def test_publish_ticket_created_puts_message_on_queue(self):
    publish_ticket_created(ticket_id)
```

**Reemplazo sugerido:**
```python
# ✅ NUEVO - Test de integración con nueva arquitectura
from .infrastructure.event_publisher import RabbitMQEventPublisher
from .domain.events import TicketCreated

def test_event_publisher_integration(self):
    publisher = RabbitMQEventPublisher()
    event = TicketCreated(
        occurred_at=datetime.now(),
        ticket_id=123,
        title="Test",
        description="Desc",
        status="OPEN"
    )
    publisher.publish(event)
    # Verificar que el mensaje llegó a RabbitMQ
```

---

## 3. ❌ Responsabilidades Eliminadas del ViewSet

### ANTES (responsabilidades excesivas):
```python
class TicketViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        # ❌ Acceso directo al ORM
        ticket = serializer.save()
        
        # ❌ Publicación de eventos desde la vista
        publish_ticket_created(ticket.id)
    
    @action(detail=True, methods=["patch"])
    def change_status(self, request, pk=None):
        # ❌ Acceso directo al ORM
        ticket = self.get_object()
        
        # ❌ Cambio de estado sin validación de reglas
        ticket.status = new_status
        ticket.save()
```

**Responsabilidades eliminadas:**
1. ❌ Acceso directo al ORM Django
2. ❌ Publicación directa de eventos a RabbitMQ
3. ❌ Lógica de negocio (validación de estados)
4. ❌ Manejo de persistencia

### DESPUÉS (solo traducción HTTP):
```python
class TicketViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        # ✅ Solo crea comando y ejecuta caso de uso
        command = CreateTicketCommand(...)
        domain_ticket = self.create_ticket_use_case.execute(command)
    
    @action(detail=True, methods=["patch"])
    def change_status(self, request, pk=None):
        # ✅ Solo valida entrada HTTP y ejecuta caso de uso
        command = ChangeTicketStatusCommand(...)
        domain_ticket = self.change_status_use_case.execute(command)
```

**Responsabilidades actuales:**
1. ✅ Validar entrada HTTP
2. ✅ Crear comandos desde datos HTTP
3. ✅ Ejecutar casos de uso
4. ✅ Traducir respuestas a HTTP
5. ✅ Manejar excepciones de dominio

---

## 4. ⚠️ Configuraciones que ya NO son necesarias

### Variables de entorno (mantener pero ya no se usan directamente en views)

Antes, las vistas accedían directamente a:
```python
# ❌ Acceso directo desde views (eliminado)
RABBIT_HOST = os.environ.get('RABBITMQ_HOST')
EXCHANGE_NAME = os.environ.get('RABBITMQ_EXCHANGE_NAME')
```

Ahora, solo las usa el adaptador:
```python
# ✅ Acceso encapsulado en el adaptador
class RabbitMQEventPublisher:
    def __init__(self):
        self.host = os.environ.get('RABBITMQ_HOST')
        self.exchange_name = os.environ.get('RABBITMQ_EXCHANGE_NAME')
```

**Acción:** Las variables siguen siendo necesarias, pero su acceso está encapsulado.

---

## 5. 🔄 Modelo Django (SIN CAMBIOS - mantener)

```python
# ✅ MANTENER - Necesario para persistencia
class Ticket(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(...)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Razón para mantener:**
- Django ORM requiere el modelo para persistencia
- El `DjangoTicketRepository` lo usa para traducir a/desde entidades de dominio
- No contiene lógica de negocio (solo definición de campos)
- Es parte de la capa de infraestructura

---

## 📋 Plan de Acción Recomendado

### Fase 1: Deprecar (sin romper tests existentes)

1. **Marcar funciones antiguas como deprecadas:**

```python
# tickets/messaging/events.py

import warnings

def publish_ticket_created(ticket_id):
    """
    DEPRECADO: Usar RabbitMQEventPublisher en su lugar.
    
    Esta función será eliminada en la próxima versión.
    Migrar a:
        from tickets.infrastructure.event_publisher import RabbitMQEventPublisher
        publisher = RabbitMQEventPublisher()
        event = TicketCreated(...)
        publisher.publish(event)
    """
    warnings.warn(
        "publish_ticket_created está deprecado. "
        "Usar RabbitMQEventPublisher",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Implementación original (mantener temporalmente)
    connection = pika.BlockingConnection(...)
    # ...
```

### Fase 2: Actualizar Tests

2. **Crear nuevos tests para la arquitectura DDD:**
   - ✅ Ya creado: `tickets/test_ddd.py`
   - ⚠️ Actualizar: `tickets/tests.py` (tests antiguos)
   - ⚠️ Actualizar: `tickets/test_integration.py`

3. **Ejecutar suite completa de tests:**
```bash
cd backend/ticket-service
python manage.py test tickets
```

### Fase 3: Eliminar Código Obsoleto

4. **Eliminar directorio `messaging/` completo:**
```bash
rm -rf tickets/messaging/
```

5. **Eliminar tests obsoletos que prueban implementación antigua**

6. **Verificar que no haya imports rotos:**
```bash
grep -r "from .messaging" tickets/
grep -r "publish_ticket_created" tickets/
```

---

## ✅ Verificación Final

### Checklist antes de eliminar:

- [ ] Todos los tests nuevos (DDD) pasan
- [ ] No hay imports de `tickets.messaging` en código de producción
- [ ] El ViewSet usa solo casos de uso (no `publish_ticket_created`)
- [ ] Los tests antiguos se han actualizado o eliminado
- [ ] La funcionalidad HTTP es idéntica (endpoints, respuestas)
- [ ] Los eventos se publican correctamente a RabbitMQ

### Comando para verificar:

```bash
# No debe devolver resultados en código de producción (solo tests):
grep -r "messaging.events" tickets/*.py
```

---

## 📊 Resumen de Cambios

| Componente | Estado | Acción |
|------------|--------|--------|
| `messaging/events.py` | ❌ Obsoleto | Deprecar → Eliminar |
| `messaging/rabbitmq.py` | ❌ Vacío | Eliminar |
| `messaging/__init__.py` | ❌ Vacío | Eliminar |
| `tests.py` (tests antiguos) | ⚠️ Desactualizado | Actualizar/Eliminar |
| `test_integration.py` | ⚠️ Desactualizado | Actualizar |
| `test_ddd.py` | ✅ Nuevo | Mantener |
| ViewSet (acceso ORM) | ❌ Eliminado | ✅ Refactorizado |
| ViewSet (publish directo) | ❌ Eliminado | ✅ Refactorizado |
| `models.py` | ✅ Necesario | Mantener |
| `serializer.py` | ✅ Compatible | Mantener |

---

## 🎯 Beneficios de la Limpieza

1. **Claridad**: Sin código duplicado o contradictorio
2. **Mantenibilidad**: Solo hay una forma de hacer las cosas
3. **Testabilidad**: Tests prueban la arquitectura correcta
4. **Documentación**: El código refleja el diseño actual
5. **Evolución**: Más fácil agregar features sobre base limpia

---

## 📚 Referencias

- [ARCHITECTURE_DDD.md](ARCHITECTURE_DDD.md) - Nueva arquitectura
- [BEFORE_AFTER.md](BEFORE_AFTER.md) - Comparación código antiguo vs nuevo
- [test_ddd.py](tickets/test_ddd.py) - Tests actualizados
