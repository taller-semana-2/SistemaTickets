# Auditoría de Deuda Técnica y Violaciones de Principios SOLID

**Proyecto:** Sistema de Tickets - Arquitectura de Microservicios  
**Fecha:** 10 de febrero de 2026  
**Auditor:** GitHub Copilot (IA)

---

## 📋 Resumen Ejecutivo

Esta auditoría identifica **12 problemas críticos** relacionados con violaciones de principios SOLID, code smells y deuda técnica que impactan la **escalabilidad, mantenibilidad y testabilidad** del sistema.

**Severidad:**
- 🔴 **Alta:** 5 problemas
- 🟡 **Media:** 5 problemas
- 🟢 **Baja:** 2 problemas

---

## 🔴 PROBLEMAS CRÍTICOS (Alta Severidad)

### 1. Violación de SRP: ViewSet con múltiples responsabilidades

**Archivo:** `backend/ticket-service/tickets/views.py`  
**Líneas:** 9-36

**Hallazgo:**
```python
class TicketViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        ticket = serializer.save()
        publish_ticket_created(ticket.id)  # ❌ Responsabilidad adicional
```

**Principio vulnerado:** Single Responsibility Principle (SRP)

**Problema:**
- El ViewSet no solo maneja HTTP requests/responses, sino que también **publica eventos a RabbitMQ** directamente.
- Mezcla lógica de presentación con lógica de negocio e integración.

**Impacto en escalabilidad:**
- **Alto:** Si el broker falla, las creaciones de tickets fallan también.
- Dificulta testing (requiere mock de RabbitMQ en tests unitarios).
- Viola el principio de separación de concerns en arquitectura de microservicios.

**Recomendación:**
Implementar un patrón **Service Layer** o usar **Django Signals** para desacoplar:
```python
# Solución propuesta
class TicketService:
    def create_ticket(self, data):
        ticket = Ticket.objects.create(**data)
        EventPublisher.publish("ticket.created", ticket.id)
        return ticket
```

---

### 2. Violación de DIP: Acoplamiento directo a Pika (RabbitMQ)

**Archivo:** `backend/ticket-service/tickets/messaging/events.py`  
**Líneas:** 8-24

**Hallazgo:**
```python
def publish_ticket_created(ticket_id):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST)  # ❌ Acoplamiento fuerte
    )
    channel = connection.channel()
    # ...
```

**Principio vulnerado:** Dependency Inversion Principle (DIP)

**Problema:**
- Dependencia directa y rígida de la librería `pika` (implementación concreta).
- Código duplicado en todos los servicios (3 veces).
- Imposible cambiar de broker sin reescribir código en múltiples lugares.

**Impacto en escalabilidad:**
- **Alto:** Si se requiere cambiar a Kafka, AWS SQS, o Azure Service Bus, hay que modificar múltiples archivos.
- No se pueden probar eventos sin RabbitMQ real.
- Viola el principio de abstracción sobre implementación.

**Recomendación:**
Crear una abstracción `MessageBroker` con inyección de dependencias:
```python
# Abstracción
class MessageBroker(ABC):
    @abstractmethod
    def publish(self, exchange, message): pass

# Implementación
class RabbitMQBroker(MessageBroker):
    def publish(self, exchange, message):
        # Implementación con pika
        pass
```

---

### 3. Gestión de recursos sin Context Manager

**Archivo:** `backend/ticket-service/tickets/messaging/events.py`  
**Líneas:** 8-23

**Hallazgo:**
```python
def publish_ticket_created(ticket_id):
    connection = pika.BlockingConnection(...)
    # ... operaciones
    connection.close()  # ❌ Si hay excepción, no se ejecuta
```

**Code Smell:** Resource Leak, falta de manejo de excepciones

**Problema:**
- Si `channel.basic_publish()` falla, la conexión nunca se cierra.
- Cada evento **crea y cierra una conexión** (ineficiente).
- Sin reintentos ni circuit breaker.

**Impacto en escalabilidad:**
- **Alto:** Memory leaks en producción bajo alta carga.
- Agotamiento del pool de conexiones de RabbitMQ.
- Degradación del rendimiento.

**Recomendación:**
```python
# Solución con context manager y connection pooling
class RabbitMQConnection:
    def __enter__(self):
        self.connection = pika.BlockingConnection(...)
        return self.connection.channel()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

def publish_ticket_created(ticket_id):
    with RabbitMQConnection() as channel:
        # ... operaciones
```

---

### 4. Valores hardcodeados y configuración dispersa

**Archivos:**
- `backend/ticket-service/tickets/messaging/events.py` (línea 5-6)
- `backend/assignment-service/messaging/consumer.py` (línea 14-16)
- `backend/notification-service/notifications/messaging/consumer.py` (línea 15-17)

**Hallazgo:**
```python
RABBIT_HOST = "rabbitmq"  # ❌ Hardcoded
EXCHANGE_NAME = "ticket_events"  # ❌ Hardcoded
QUEUE_NAME = 'assignment_queue'  # ❌ Hardcoded
```

**Code Smell:** Magic Strings, configuración duplicada

**Problema:**
- Configuración duplicada en **3 servicios**.
- Cambiar el nombre del exchange requiere modificar múltiples archivos.
- No se usa variables de entorno consistentemente (en algunos sí, en otros no).

**Impacto en escalabilidad:**
- **Medio:** Dificulta despliegue en múltiples ambientes (dev, staging, prod).
- Aumenta riesgo de errores de configuración.
- No sigue el principio de [12-Factor App](https://12factor.net/).

**Recomendación:**
```python
# Centralizar en settings o usar .env
class MessageConfig:
    RABBIT_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    EXCHANGE_NAME = os.getenv('EXCHANGE_NAME', 'ticket_events')
    QUEUE_NAME = os.getenv('QUEUE_NAME', 'assignment_queue')
```

---

### 5. Validación insuficiente y lógica de negocio débil

**Archivo:** `backend/ticket-service/tickets/views.py`  
**Líneas:** 18-33

**Hallazgo:**
```python
@action(detail=True, methods=["patch"], url_path="status")
def change_status(self, request, pk=None):
    new_status = request.data.get("status")
    if not new_status:  # ❌ Solo valida presencia
        return Response(...)
    ticket.status = new_status  # ❌ No valida transiciones válidas
    ticket.save()
```

**Principio vulnerado:** SRP + Domain Logic fuera del modelo

**Problema:**
- No valida que la transición sea válida (ej: CLOSED → OPEN podría no tener sentido).
- Lógica de negocio en el ViewSet en lugar del modelo o servicio.
- No hay máquina de estados definida.

**Impacto en escalabilidad:**
- **Medio:** Inconsistencias de datos a medida que crece el sistema.
- Dificulta agregar reglas de negocio (ej: solo admin puede reabrir tickets cerrados).
- Código difícil de testear unitariamente.

**Recomendación:**
```python
# En el modelo
class Ticket(models.Model):
    VALID_TRANSITIONS = {
        'OPEN': ['IN_PROGRESS', 'CLOSED'],
        'IN_PROGRESS': ['CLOSED', 'OPEN'],
        'CLOSED': []
    }
    
    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])
    
    def change_status(self, new_status):
        if not self.can_transition_to(new_status):
            raise InvalidTransition(...)
        self.status = new_status
        self.save()
```

---

## 🟡 PROBLEMAS MODERADOS (Media Severidad)

### 6. Duplicación de código en consumers

**Archivos:**
- `backend/assignment-service/messaging/consumer.py`
- `backend/notification-service/notifications/messaging/consumer.py`

**Hallazgo:**
Ambos consumers tienen **casi el mismo código** (90% duplicado):
```python
# Setup de Django idéntico (9 líneas)
# Declaración de exchange idéntica
# Declaración de cola similar
# Lógica de binding idéntica
```

**Code Smell:** Copy-Paste Programming, DRY violation

**Problema:**
- Código duplicado en 2 archivos.
- Si hay un bug en la configuración, hay que arreglarlo 2 veces.
- Si se agrega un tercer servicio, se duplicará de nuevo.

**Impacto en escalabilidad:**
- **Medio:** Aumenta el costo de mantenimiento.
- Mayor superficie para bugs.
- Dificulta evolución del sistema.

**Recomendación:**
Crear una clase base `BaseConsumer`:
```python
class BaseConsumer:
    def __init__(self, queue_name, callback):
        self.queue_name = queue_name
        self.callback = callback
    
    def start_consuming(self):
        # Lógica común
        pass
```

---

### 7. Ausencia de tipado (Type Hints)

**Archivo:** Todo el código Python

**Hallazgo:**
Ningún archivo usa **type hints** de Python 3.5+:
```python
# ❌ Actual
def publish_ticket_created(ticket_id):
    pass

# ✅ Recomendado
def publish_ticket_created(ticket_id: int) -> None:
    pass
```

**Code Smell:** Falta de documentación implícita, propenso a errores

**Impacto en escalabilidad:**
- **Medio:** Dificulta onboarding de nuevos desarrolladores.
- Aumenta bugs por tipos incorrectos.
- IDEs no pueden proveer autocompletado efectivo.

**Recomendación:**
Agregar type hints y usar `mypy` para validación estática.

---

### 8. Falta de manejo de errores en consumers

**Archivo:** `backend/notification-service/notifications/messaging/consumer.py`  
**Líneas:** 20-25

**Hallazgo:**
```python
def callback(ch, method, properties, body):
    data = json.loads(body)  # ❌ Puede fallar
    ticket_id = data.get('ticket_id')  # ❌ Puede ser None
    Notification.objects.create(...)  # ❌ Puede fallar
    ch.basic_ack(...)  # ✅ Siempre reconoce, incluso si falló
```

**Code Smell:** Error Swallowing, falta de robustez

**Problema:**
- Si `json.loads` falla, el consumer se cae.
- Si la DB está down, el mensaje se pierde (ACK exitoso).
- No hay logging de errores estructurado.

**Impacto en escalabilidad:**
- **Medio:** Pérdida de eventos en producción.
- Dificulta debugging de incidentes.
- Sistema no tolera fallos parciales.

**Recomendación:**
```python
def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        ticket_id = data['ticket_id']  # Requerir, no usar .get()
        Notification.objects.create(...)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON: {body}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Error processing: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
```

---

### 9. Uso de `random.choice()` en lógica de negocio

**Archivo:** `backend/assignment-service/messaging/handlers.py`  
**Línea:** 6

**Hallazgo:**
```python
def handle_ticket_created(ticket_id):
    priority = random.choice(["high", "medium", "low"])  # ❌
```

**Code Smell:** Non-deterministic business logic

**Problema:**
- La prioridad es completamente aleatoria (no hay reglas de negocio).
- Impossible de testear de forma determinística.
- No agrega valor real al sistema.

**Impacto en escalabilidad:**
- **Bajo:** Funcionalidad placeholder sin valor.
- Confunde sobre el propósito del servicio.

**Recomendación:**
Implementar lógica real basada en keywords, urgencia, o ML:
```python
def calculate_priority(ticket_id):
    ticket = get_ticket_details(ticket_id)
    if 'urgent' in ticket.title.lower():
        return 'high'
    # ... lógica real
```

---

### 10. Falta de índices en consultas frecuentes

**Archivo:** `backend/ticket-service/tickets/views.py`  
**Línea:** 10

**Hallazgo:**
```python
queryset = Ticket.objects.all().order_by("-created_at")
```

**Problema:**
- `created_at` no tiene índice definido en el modelo.
- Consulta `all()` sin paginación configurada.
- Crecimiento lineal del tiempo de respuesta.

**Impacto en escalabilidad:**
- **Medio:** Performance degradada con >10k tickets.
- Queries lentas sin índices.

**Recomendación:**
```python
# En models.py
class Ticket(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'status']),
        ]
```

---

## 🟢 PROBLEMAS MENORES (Baja Severidad)

### 11. Secret key hardcoded en settings

**Archivo:** `backend/ticket-service/ticket_service/settings.py`  
**Línea:** 23

**Hallazgo:**
```python
SECRET_KEY = 'django-insecure-(060&9*4y4r9r8expw#76^v9ozrag0wlbrc3er8---@kg)&f#4'
```

**Code Smell:** Security vulnerability

**Problema:**
- Secret key en el repositorio (expuesta en Git).
- Misma key en dev y prod.

**Impacto:**
- **Bajo (en dev):** Riesgo de seguridad si se usa en producción.

**Recomendación:**
```python
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-insecure-key')
```

---

### 12. Serializer con `fields = "__all__"`

**Archivo:** `backend/ticket-service/tickets/serializer.py`  
**Línea:** 6

**Hallazgo:**
```python
class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"  # ❌
```

**Code Smell:** Over-exposure, lack of explicit contract

**Problema:**
- Expone todos los campos del modelo (incluso sensibles si se agregan).
- No define un contrato explícito API.

**Impacto:**
- **Bajo:** Potencial exposición de datos no deseados.

**Recomendación:**
```python
fields = ['id', 'title', 'description', 'status', 'created_at']
```

---

## 📊 Resumen de Impactos

| Problema | Principio SOLID | Impacto Escalabilidad | Esfuerzo Fix |
|----------|-----------------|----------------------|--------------|
| ViewSet con múltiples responsabilidades | SRP | 🔴 Alto | Medio |
| Acoplamiento a Pika | DIP | 🔴 Alto | Alto |
| Gestión de recursos deficiente | N/A | 🔴 Alto | Bajo |
| Configuración hardcoded | N/A | 🟡 Medio | Bajo |
| Validación de estado débil | SRP | 🟡 Medio | Medio |
| Código duplicado en consumers | DRY | 🟡 Medio | Medio |
| Sin type hints | N/A | 🟡 Medio | Bajo |
| Sin manejo de errores | N/A | 🟡 Medio | Medio |
| Lógica aleatoria | N/A | 🟢 Bajo | Bajo |
| Sin índices DB | N/A | 🟡 Medio | Bajo |
| Secret key hardcoded | N/A | 🟢 Bajo | Muy Bajo |
| Serializer expone todo | OCP | 🟢 Bajo | Muy Bajo |

---

## 🎯 Recomendaciones Prioritarias

### Corto Plazo (Sprint 1-2):
1. ✅ Implementar Service Layer (problema #1)
2. ✅ Context managers para RabbitMQ (problema #3)
3. ✅ Validación de transiciones de estado (problema #5)
4. ✅ Manejo de errores en consumers (problema #8)
5. ✅ Mover secrets a variables de entorno (problema #11)

### Mediano Plazo (Sprint 3-4):
6. ✅ Crear abstracción MessageBroker (problema #2)
7. ✅ Eliminar duplicación en consumers (problema #6)
8. ✅ Agregar índices DB (problema #10)
9. ✅ Centralizar configuración (problema #4)

### Largo Plazo (Refactor):
10. ✅ Agregar type hints completos (problema #7)
11. ✅ Implementar lógica real de prioridad (problema #9)
12. ✅ Hacer explícitos los serializers (problema #12)

---

## 📚 Referencias

- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [12-Factor App](https://12factor.net/)
- [Refactoring Guru - Code Smells](https://refactoring.guru/refactoring/smells)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)

---

**Fin del reporte de auditoría.**
