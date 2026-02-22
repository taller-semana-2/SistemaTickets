# PROMPT_BUG_012 — Instrucciones para Agentes AI

## Resumen Ejecutivo

**Bug:** BUG-012 — Los consumers RabbitMQ de `notification-service` y `assignment-service` crashean sin reintentos al perder la conexión con RabbitMQ.

**Branch:** `fix/bug-012-rabbitmq-reconnection`

**Repositorio (fork):** https://github.com/taller-semana-2/SistemaTickets

**Base branch:** `develop`

**Objetivo:** Implementar reconexión automática con backoff exponencial en ambos consumers, cumpliendo los criterios de aceptación de [BUG_012.md](BUG_012.md) y las reglas de `.github/instructions/rabbitmq.instructions.md`.

---

## 1. Contexto Técnico para el Orchestrator

### 1.1 Archivos afectados

| Servicio | Archivo consumer | Líneas clave |
|---|---|---|
| notification-service | `backend/notification-service/notifications/messaging/consumer.py` | `start_consuming()` L147-184 |
| assignment-service | `backend/assignment-service/messaging/consumer.py` | `start_consuming()` L39-56 |

### 1.2 Estado actual del código

**notification-service** `start_consuming()`:
```python
def start_consuming():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print(f'[NOTIFICATION] Consumer started, waiting messages on queue "{QUEUE_NAME}"...')
    channel.start_consuming()
```

**assignment-service** `start_consuming()`:
```python
def start_consuming():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST)
    )
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print(f"[ASSIGNMENT] Esperando eventos en cola '{QUEUE_NAME}'...")
    channel.start_consuming()
```

**Problema:** Ninguno de los dos tiene `try/except` alrededor de la conexión o el consuming loop. Si RabbitMQ se cae o la conexión se pierde, `pika.exceptions.AMQPConnectionError` o `pika.exceptions.StreamLostError` crashean el proceso.

### 1.3 Infraestructura Docker relevante

- `assessment-consumer`: contenedor dedicado que ejecuta `python messaging/consumer.py` con `restart: on-failure`
- `notification-consumer`: contenedor dedicado que ejecuta `python notifications/messaging/consumer.py` con `restart: on-failure`
- `notification-service` entrypoint.sh: también lanza el consumer en background vía `python -m notifications.messaging.consumer &`

Nota: `restart: on-failure` en Docker da cierta resiliencia, pero los contenedores reinician completos (pérdida de estado, logs confusos, delay alto). La reconexión interna del consumer es más eficiente y controlada.

### 1.4 Dependencias disponibles

- `pika>=1.3.0` — ya instalado en ambos servicios
- No se requieren dependencias adicionales; `time` y `logging` son stdlib

---

## 2. Prompt para el Orchestrator Agent

> Copia este bloque completo como prompt para el agente Orchestrator.

---

### PROMPT START

```
Eres el agente Orchestrator coordinando la resolución de BUG-012.

Repositorio: https://github.com/taller-semana-2/SistemaTickets
Branch de trabajo: fix/bug-012-rabbitmq-reconnection (basada en develop)

## Problema
Los consumers RabbitMQ de notification-service y assignment-service crashean
sin reintentos cuando la conexión a RabbitMQ se pierde (AMQPConnectionError,
StreamLostError, ConnectionClosedByBroker). El proceso muere y no vuelve a
procesar mensajes hasta un restart manual del contenedor.

## Objetivo
Implementar reconexión automática con backoff exponencial en ambos consumers.

## Archivos a modificar
1. backend/notification-service/notifications/messaging/consumer.py
2. backend/assignment-service/messaging/consumer.py

## Plan de trabajo (delegar a Planner → Coder)

### Fase 1 — Diseño (Planner)
Diseñar la estrategia de reconexión antes de codificar:

1. **Patrón:** Loop infinito externo que envuelve la creación de conexión +
   start_consuming(). Al capturar excepción de conexión, esperar con backoff
   exponencial y reintentar.

2. **Configuración de backoff:**
   - INITIAL_RETRY_DELAY = 1 segundo
   - MAX_RETRY_DELAY = 60 segundos
   - RETRY_BACKOFF_FACTOR = 2
   - MAX_RETRIES = 0 (infinito por defecto; configurable por env var)
   - Fórmula: delay = min(INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** attempt), MAX_RETRY_DELAY)

3. **Excepciones a capturar:**
   - pika.exceptions.AMQPConnectionError
   - pika.exceptions.StreamLostError
   - pika.exceptions.ConnectionClosedByBroker
   - ConnectionResetError
   - Exception (catch-all con logging de error inesperado)

4. **Logging requerido:**
   - INFO al conectar exitosamente
   - WARNING en cada intento de reconexión (con número de intento y delay)
   - INFO al reconectar exitosamente (resetear contador)
   - CRITICAL si se alcanza MAX_RETRIES > 0 y se agotan los reintentos
   - Usar logger de Python (logging module), NO print()

5. **Reducción de duplicación (regla del proyecto):**
   El ~90% del setup de conexión es idéntico entre ambos consumers.
   Considerar si vale la pena extraer la lógica de reconexión a una función
   reutilizable o dejarla inline en cada consumer. Decisión pragmática:
   dado que son solo 2 archivos y cada uno tiene su propio callback, la
   implementación inline con el mismo patrón es aceptable. Si en el futuro
   un tercer servicio necesita consumer, entonces extraer.

6. **Cleanup de conexión:**
   En el bloque except, intentar cerrar la conexión existente de forma
   segura (connection.close() envuelto en try/except silencioso) antes
   de reintentar.

### Fase 2 — Implementación (Coder)
Modificar los dos archivos consumer.py aplicando el patrón diseñado.

Para **notification-service** (`backend/notification-service/notifications/messaging/consumer.py`):
- Reemplazar la función start_consuming() (líneas 147-184)
- Mantener intactos: imports, variables de entorno, callback(),
  _handle_response_added(), _handle_ticket_created()
- Convertir print() existentes a logger.info()
- Agregar constantes de configuración de backoff al inicio del archivo
  (después de las variables RABBIT_HOST, EXCHANGE_NAME, QUEUE_NAME)

Para **assignment-service** (`backend/assignment-service/messaging/consumer.py`):
- Reemplazar la función start_consuming() (líneas 39-56)
- Mantener intactos: imports, variables de entorno, callback()
- Convertir print() existentes a logger.info() / logger.error()
- Agregar import logging + logger + constantes de configuración

Estructura esperada de start_consuming() tras el cambio:
```python
def start_consuming() -> None:
    attempt = 0
    while True:
        try:
            logger.info("Connecting to RabbitMQ at %s...", RABBIT_HOST)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

            logger.info("Consumer started, waiting for messages on queue '%s'...", QUEUE_NAME)
            attempt = 0  # Reset on successful connection
            channel.start_consuming()

        except (pika.exceptions.AMQPConnectionError,
                pika.exceptions.StreamLostError,
                pika.exceptions.ConnectionClosedByBroker,
                ConnectionResetError) as exc:
            attempt += 1
            delay = min(
                INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** attempt),
                MAX_RETRY_DELAY,
            )
            logger.warning(
                "Connection lost (%s). Reconnection attempt %d in %.1fs...",
                exc, attempt, delay,
            )
            _safe_close(connection)
            time.sleep(delay)

            if MAX_RETRIES > 0 and attempt >= MAX_RETRIES:
                logger.critical(
                    "Max reconnection attempts (%d) reached. Shutting down.",
                    MAX_RETRIES,
                )
                sys.exit(1)

        except KeyboardInterrupt:
            logger.info("Consumer stopped by user.")
            _safe_close(connection)
            break

        except Exception as exc:
            attempt += 1
            delay = min(
                INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** attempt),
                MAX_RETRY_DELAY,
            )
            logger.error(
                "Unexpected error (%s). Reconnection attempt %d in %.1fs...",
                exc, attempt, delay,
            )
            _safe_close(connection)
            time.sleep(delay)

            if MAX_RETRIES > 0 and attempt >= MAX_RETRIES:
                logger.critical(
                    "Max reconnection attempts (%d) reached. Shutting down.",
                    MAX_RETRIES,
                )
                sys.exit(1)
```

Función helper:
```python
def _safe_close(connection) -> None:
    """Intenta cerrar la conexión de forma segura."""
    try:
        if connection and connection.is_open:
            connection.close()
    except Exception:
        pass
```

Constantes a agregar:
```python
# Reconnection configuration
INITIAL_RETRY_DELAY: int = int(os.environ.get('RABBITMQ_INITIAL_RETRY_DELAY', '1'))
MAX_RETRY_DELAY: int = int(os.environ.get('RABBITMQ_MAX_RETRY_DELAY', '60'))
RETRY_BACKOFF_FACTOR: int = int(os.environ.get('RABBITMQ_RETRY_BACKOFF_FACTOR', '2'))
MAX_RETRIES: int = int(os.environ.get('RABBITMQ_MAX_RETRIES', '0'))  # 0 = infinite
```

### Fase 3 — Testing (Coder)
Crear tests unitarios para la lógica de reconexión en ambos servicios.

**Archivo:** `backend/notification-service/notifications/messaging/test_consumer_reconnection.py`
**Archivo:** `backend/assignment-service/messaging/test_consumer_reconnection.py`

Tests requeridos:
1. test_backoff_delay_calculation — Verificar que el delay sigue la fórmula
   exponencial y no excede MAX_RETRY_DELAY
2. test_reconnection_on_amqp_error — Mock de pika.BlockingConnection que lanza
   AMQPConnectionError; verificar que se reintenta y se logea WARNING
3. test_reconnection_resets_attempt_on_success — Tras reconexión exitosa,
   simular nueva pérdida y verificar que attempt vuelve a 1
4. test_max_retries_triggers_shutdown — Con MAX_RETRIES=3, verificar que
   tras 3 fallos se logea CRITICAL y se llama sys.exit(1)
5. test_safe_close_handles_exception — Verificar que _safe_close no lanza
   excepciones aunque connection.close() falle
6. test_keyboard_interrupt_graceful_shutdown — Verificar que KeyboardInterrupt
   cierra la conexión y sale limpiamente

Patrón de testing:
- Usar unittest.mock.patch para mockear pika.BlockingConnection
- Usar unittest.mock.patch para mockear time.sleep (no esperar en tests)
- Usar unittest.mock.patch para mockear sys.exit
- NO depender de Django en los tests de reconexión (lógica pura Python)

### Fase 4 — Validación (Orchestrator)
1. Verificar que ambos consumers funcionan localmente:
   ```bash
   docker compose up --build notification-consumer assessment-consumer rabbitmq
   ```
2. Simular pérdida de conexión:
   ```bash
   docker stop rabbitmq
   # Observar logs de consumers: deben mostrar WARNING con backoff
   docker start rabbitmq
   # Observar logs: deben mostrar INFO de reconexión exitosa
   ```
3. Ejecutar tests:
   ```bash
   cd backend/notification-service && python -m pytest notifications/messaging/test_consumer_reconnection.py -v
   cd backend/assignment-service && python -m pytest messaging/test_consumer_reconnection.py -v
   ```
4. Quality Gate: Aplicar checklist de AI_WORKFLOW.md antes del commit:
   - ¿Existe acoplamiento innecesario? → No, cambio contenido en capa messaging
   - ¿La lógica de dominio está claramente separada? → Sí, no se toca dominio
   - ¿El código es testeable? → Sí, función pura con mocks
   - ¿Los handlers de eventos son idempotentes? → No se modifican handlers
   - ¿Se introducen configuraciones frágiles? → No, defaults hardcoded + env vars
   - ¿Se incrementa la deuda técnica? → No, se reduce

## REGLAS OBLIGATORIAS (del proyecto)
- NO modificar lógica de dominio, handlers ni callbacks — son correctos
- NO agregar dependencias nuevas
- Usar logging (módulo estándar), NO print()
- Consumer ya tiene restart: on-failure en Docker; la reconexión interna
  es complementaria, no lo reemplaza
- Los consumers son idempotentes por diseño (ver callbacks existentes:
  notification usa basic_ack siempre, assignment delega a Celery)
- Mantener compatibilidad con entrypoint.sh de notification-service
  que lanza consumer en background
- Type hints en funciones nuevas (alineado con coding philosophy)
```

### PROMPT END

---

## 3. Instrucciones por Agente

### 3.1 Planner

**Responsabilidad:** Validar y refinar el plan de la Fase 1 antes de pasar a Coder.

**Checklist del Planner:**
- [ ] ¿El patrón de backoff exponencial cubre todos los escenarios de pérdida de conexión?
- [ ] ¿Se manejan las excepciones correctas de pika?
- [ ] ¿La configuración es parametrizable por variables de entorno?
- [ ] ¿Se contempla el graceful shutdown con KeyboardInterrupt?
- [ ] ¿Los tests propuestos cubren los 3 escenarios Gherkin de BUG_012.md?
- [ ] ¿Se respeta la separación de capas (el cambio solo toca infrastructure/messaging)?

**Output esperado:** Plan refinado con cualquier ajuste, listo para Coder.

---

### 3.2 Coder

**Responsabilidad:** Implementar cambios en los 2 archivos consumer.py + crear 2 archivos de test.

**Archivos a crear/modificar:**

| Acción | Archivo |
|---|---|
| MODIFICAR | `backend/notification-service/notifications/messaging/consumer.py` |
| MODIFICAR | `backend/assignment-service/messaging/consumer.py` |
| CREAR | `backend/notification-service/notifications/messaging/test_consumer_reconnection.py` |
| CREAR | `backend/assignment-service/messaging/test_consumer_reconnection.py` |

**Reglas de implementación para el Coder:**

1. **import time** — agregar al inicio de ambos archivos
2. **import logging** — ya existe en notification-service; agregar en assignment-service
3. **logger** — ya existe en notification-service como `logger = logging.getLogger(__name__)`; crear en assignment-service
4. **Constantes de backoff** — poner después de las variables de entorno RabbitMQ
5. **_safe_close()** — crear antes de start_consuming() en ambos archivos
6. **start_consuming()** — reescribir con el loop de reconexión (ver pseudocódigo en el prompt)
7. **print() → logger** — convertir todos los print() a logger.info/error
8. **Docstring** — actualizar el docstring de start_consuming() para documentar el comportamiento de reconexión
9. **`if __name__ == '__main__'`** — mantener igual en ambos
10. **NO tocar** callback(), _handle_response_added(), _handle_ticket_created(), handlers.py

**Verificación rápida antes de commitear:**
```bash
# Verificar sintaxis
python -c "import ast; ast.parse(open('backend/notification-service/notifications/messaging/consumer.py').read())"
python -c "import ast; ast.parse(open('backend/assignment-service/messaging/consumer.py').read())"
```

---

### 3.3 Designer

**Responsabilidad:** No aplica para este bug. No hay cambios de frontend/UI.

---

## 4. Criterios de Aceptación (referencia de BUG_012.md)

```gherkin
@bug:BUG-012 @priority:alta
Feature: Reconexión automática de consumers RabbitMQ
  Como operador del sistema
  Quiero que los consumers se reconecten automáticamente a RabbitMQ
  Para evitar pérdida de procesamiento de mensajes

  Scenario: Reconexión tras pérdida de conexión
    Given el consumer está conectado y procesando mensajes
    When la conexión a RabbitMQ se pierde
    Then el consumer intenta reconectarse automáticamente
    And usa backoff exponencial entre reintentos
    And logea cada intento de reconexión

  Scenario: Reconexión exitosa reanuda procesamiento
    Given el consumer perdió la conexión y está intentando reconectarse
    When la conexión se restablece
    Then el consumer reanuda el procesamiento de mensajes
    And logea la reconexión exitosa

  Scenario: Máximo de reintentos alcanzado
    Given el consumer ha intentado reconectarse el máximo de veces configurado
    When todos los reintentos fallan
    Then el consumer logea un error crítico
    And el proceso termina de forma controlada (no crash silencioso)
```

---

## 5. Definición de Done

- [ ] `start_consuming()` de notification-service tiene reconexión con backoff exponencial
- [ ] `start_consuming()` de assignment-service tiene reconexión con backoff exponencial
- [ ] Todos los `print()` convertidos a `logger.info/warning/error`
- [ ] Constantes de backoff configurables por env vars con defaults sensatos
- [ ] `_safe_close()` implementada en ambos consumers
- [ ] KeyboardInterrupt produce shutdown limpio
- [ ] MAX_RETRIES configurable (0 = infinito)
- [ ] 6+ tests unitarios por servicio, todos pasando
- [ ] Tests no dependen de Django ni de RabbitMQ real
- [ ] Quality Gate (AI_WORKFLOW) ejecutado y aprobado
- [ ] Branch `fix/bug-012-rabbitmq-reconnection` lista para PR contra `develop`
- [ ] PR creada en https://github.com/taller-semana-2/SistemaTickets

---

## 6. Contexto adicional del proyecto

### Reglas clave a respetar

- **rabbitmq.instructions.md:** "auto reconnect on failure", "retry transient failures", "log errors"
- **backend-ddd.instructions.md:** "Messaging handlers must: Parse message → Validate schema → Call use case → ACK message". Los handlers no se tocan.
- **copilot-instructions.md:** "Wrap RabbitMQ consumers in try/except", "Never crash consumer loop", "Always log structured errors"
- **AI_WORKFLOW.md:** Quality Gate obligatorio antes del commit

### Docker compose

Ambos consumers tienen `restart: on-failure` en docker-compose.yml. Esto no se modifica. La reconexión interna es complementaria: evita el overhead de reiniciar todo el contenedor y proporciona logs más claros.

### Nota sobre duplicación

El proyecto reconoce (~90% duplicación de setup de consumidores entre Assignment y Notification). Este bug fix **no** aborda esa deuda técnica — se limita a agregar reconexión. Una futura tarea puede extraer un `BaseRabbitMQConsumer` compartido.
