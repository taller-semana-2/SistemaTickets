# Test Plan — Sistema de Tickets

## Leyenda

| Símbolo | Significado |
|---|---|
| ✅ | Existe y está bien implementado |
| ⚠️ | Existe pero necesita mejoras |
| 🆕 | No existe, se recomienda crear |
---

## Principio de Pruebas Aplicable

**Principio 6: Las pruebas dependen del contexto.**

Este proyecto presenta un contexto inusualmente complejo:
- Microservicios independientes con arquitectura DDD
- Comunicación asíncrona vía RabbitMQ (eventos)
- Capa de dominio Python puro (sin Django)
- Integración entre servicios solo por eventos o REST

Una sola estrategia de testing no es suficiente. Cada capa y cada tipo de interacción requiere un enfoque distinto.

**Conexión con el incidente documentado:**
El bug del exchange `fanout` (ver [CALIDAD.md](CALIDAD.md)) no era un error de dominio — era un error de configuración de infraestructura de mensajería. Un test unitario no lo habría detectado. Solo un test de integración con el contexto correcto (broker real o simulado con exchanges) lo hubiera atrapado. Eso es exactamente lo que describe el principio 6.

---

## Niveles de Prueba

### Nivel 1 — Unitario

Prueba la lógica de dominio pura.  
**Sin Django, sin DB, sin RabbitMQ.**  
Herramienta: `pytest` + `unittest.mock`.

#### ticket-service

| # | Estado | Caso de prueba | Archivo |
|---|---|---|---|
| U1 | ✅ | `TicketFactory` crea ticket válido en estado `OPEN` con timestamp correcto | `tests/unit/test_ticket_factory.py` |
| U2 | ✅ | `TicketFactory` rechaza título vacío, con espacios o `None` | `tests/unit/test_ticket_factory.py` |
| U3 | ✅ | `TicketFactory` rechaza descripción vacía, con espacios o `None` | `tests/unit/test_ticket_factory.py` |
| U4 | ✅ | `TicketFactory` aplica strip a título y descripción | `tests/unit/test_ticket_factory.py` |
| U5 | ✅ | `CreateTicketUseCase` persiste en repositorio y publica evento `TicketCreated` | `tests/unit/test_use_cases.py` |
| U6 | ✅ | `CreateTicketUseCase` con título vacío no persiste ni publica evento | `tests/unit/test_use_cases.py` |
| U7 | ✅ | Evento publicado contiene todos los campos: `ticket_id`, `title`, `status`, `occurred_at` | `tests/unit/test_use_cases.py` |
| U8 | ✅ | `ChangeTicketStatusUseCase` actualiza estado y publica `TicketStatusChanged` con `old_status` y `new_status` | `tests/unit/test_use_cases.py` |
| U9 | ✅ | `ChangeTicketStatusUseCase` con ticket no encontrado lanza `ValueError` | `tests/unit/test_use_cases.py` |
| U10 | ✅ | Cambiar estado de ticket `CLOSED` lanza `TicketAlreadyClosed` | `tests/unit/test_use_cases.py` |
| U11 | ✅ | Cambiar al mismo estado no publica evento (idempotencia) | `tests/unit/test_use_cases.py` |
| U12 | ✅ | Múltiples cambios de estado publican múltiples eventos correctos | `tests/unit/test_use_cases.py` |
| U13 | ✅ | Eventos de dominio son inmutables (`FrozenInstanceError`) | `tests/unit/test_events.py` |
| U14 | ✅ | `ViewSet` delega a `CreateTicketUseCase` en `perform_create` | `tests/unit/test_views.py` |
| U15 | ✅ | `ViewSet` maneja `InvalidTicketData` y devuelve `ValidationError` | `tests/unit/test_views.py` |
| U16 | ⚠️ | Transición `IN_PROGRESS → CLOSED` es válida | `tests/unit/test_use_cases.py` — falta caso explícito |
| U17 | 🆕 | Transición `OPEN → CLOSED` directa debe ser inválida | Crear en `tests/unit/test_use_cases.py` |

#### notification-service

| # | Estado | Caso de prueba | Archivo |
|---|---|---|---|
| U18 | ✅ | `Notification` creada con datos válidos, `read=False` | `tests/test_domain.py` |
| U19 | ✅ | `mark_as_read()` cambia estado y genera evento `NotificationMarkedAsRead` | `tests/test_domain.py` |
| U20 | ✅ | `mark_as_read()` es idempotente (segunda llamada no genera evento) | `tests/test_domain.py` |
| U21 | ✅ | `MarkNotificationAsReadUseCase` marca como leída y publica evento | `tests/test_use_cases.py` |
| U22 | ✅ | `MarkNotificationAsReadUseCase` con notificación no encontrada lanza `NotificationNotFound` | `tests/test_use_cases.py` |
| U23 | ✅ | `MarkNotificationAsReadUseCase` ya leída no republica evento (idempotencia) | `tests/test_use_cases.py` |
| U24 | ✅ | `NotificationViewSet` delega a `MarkNotificationAsReadUseCase` y retorna `204` | `tests/test_views.py` |

#### assignment-service

| # | Estado | Caso de prueba | Archivo |
|---|---|---|---|
| U25 | ✅ | `Assignment` creado con datos válidos | `assignments/tests.py` |
| U26 | ✅ | `Assignment` rechaza `ticket_id` vacío o con solo espacios | `assignments/tests.py` |
| U27 | ✅ | `Assignment` rechaza prioridades inválidas (`urgent`, `critical`) | `assignments/tests.py` |
| U28 | ✅ | `Assignment` acepta todas las prioridades válidas (`high`, `medium`, `low`) | `assignments/tests.py` |
| U29 | ✅ | `AssignmentCreated` y `AssignmentReassigned` serializan correctamente a dict | `assignments/tests.py` |

#### users-service

| # | Estado | Caso de prueba | Archivo |
|---|---|---|---|
| U30 | ✅ | `User` creado inicia en estado activo | `tests/test_domain.py` |
| U31 | ✅ | `User` valida formato de email (`InvalidEmail`) | `tests/test_domain.py` |
| U32 | ✅ | `User` rechaza email vacío o username vacío | `tests/test_domain.py` |
| U33 | ⚠️ | `CreateUserUseCase` con email duplicado lanza `UserAlreadyExists` | `tests/test_use_cases.py` — **archivo vacío**, solo tiene código de ejemplo |
| U34 | 🆕 | `User` con rol `agent` puede ser diferenciado de rol `standard` | Crear en `tests/test_domain.py` |

---

### Nivel 2 — Integración

Prueba la interacción entre capas dentro de un mismo servicio.  
**Con DB real, y mock del broker cuando aplique.**

| # | Estado | Caso de prueba | Servicio | Archivo |
|---|---|---|---|---|
| I1 | ✅ | `DjangoTicketRepository` guarda ticket nuevo y asigna ID | ticket-service | `tests/unit/test_infrastructure.py` |
| I2 | ✅ | `DjangoTicketRepository` actualiza ticket existente en DB | ticket-service | `tests/unit/test_infrastructure.py` |
| I3 | ✅ | `DjangoTicketRepository` retorna entidad de dominio en `find_by_id` | ticket-service | `tests/unit/test_infrastructure.py` |
| I4 | ✅ | Flujo completo: crear ticket persiste en DB y publica evento (mock publisher) | ticket-service | `tests/integration/test_ticket_workflow.py` |
| I5 | ✅ | Ciclo completo OPEN → IN_PROGRESS → CLOSED con eventos correspondientes (mock publisher) | ticket-service | `tests/integration/test_ticket_workflow.py` |
| I6 | ✅ | `DjangoAssignmentRepository` guarda y recupera `Assignment` por `ticket_id` | assignment-service | `assignments/tests.py` |
| I7 | ✅ | `DjangoNotificationRepository` guarda nueva notificación y asigna ID | notification-service | `tests/test_infrastructure.py` |
| I8 | ✅ | `DjangoNotificationRepository` actualiza notificación existente (`read=True`) | notification-service | `tests/test_infrastructure.py` |
| I9 | ⚠️ | Handler de `notification-service` recibe `ticket.created` → crea `Notification` en DB | notification-service | `tests/test_integration.py` — **requiere RabbitMQ real y Docker levantado** |
| I10 | ⚠️ | Handler de `assignment-service` recibe `ticket.created` → crea `Assignment` en DB | assignment-service | `test_integration.py` — **requiere RabbitMQ real y Docker levantado** |
| I11 | ⚠️ | API y repositorio de `users-service` integrados | users-service | `tests/test_integration.py` — **archivo vacío**, solo tiene código de ejemplo |
| I12 | 🆕 | Handler recibe evento con schema inválido (campos faltantes) → no crashea el consumer | assignment-service / notification-service | Crear en `tests/` de cada servicio |
| I13 | 🆕 | Evento publicado por `ticket-service` cumple el contrato JSON completo | ticket-service | Crear en `tests/integration/` |

**Contratos de eventos a validar en I13:**

`ticket.created`:
```json
{
  "event_type": "ticket.created",
  "ticket_id": 1,
  "title": "string",
  "user_id": 1,
  "status": "open",
  "timestamp": "ISO8601"
}
```

`ticket.status_changed`:
```json
{
  "event_type": "ticket.status_changed",
  "ticket_id": 1,
  "old_status": "open",
  "new_status": "in_progress",
  "timestamp": "ISO8601"
}
```

---

### Nivel 3 — Sistema (E2E)

Prueba el flujo completo entre servicios con infraestructura real (Docker Compose).  
**Alcance mínimo: solo el happy path crítico.**

| # | Estado | Caso de prueba | Servicios involucrados | Archivo |
|---|---|---|---|---|
| S1 | ⚠️ | Publicar `ticket.created` en broker → `Assignment` creado en DB | assignment-service | `test_integration.py` — funciona pero no verifica el schema del evento |
| S2 | ⚠️ | Publicar `ticket.created` en broker → `Notification` creada en DB | notification-service | `tests/test_integration.py` — mismo problema que S1 |
| S3 | 🆕 | `POST /api/tickets/` → `Assignment` y `Notification` creados en sus respectivos servicios | ticket-service + assignment-service + notification-service | Crear test E2E unificado |

> **Nota:** El alto costo de los tests E2E en arquitecturas con mensajería asíncrona no justifica más de 2-3 casos en este contexto. (Principio 6)

---

## Resumen de brechas críticas

| Brecha | Riesgo | Prioridad |
|---|---|---|
| I11: `users-service` sin tests de integración reales | Un cambio en la API de usuarios no tiene red de seguridad | Alta |
| I12: Consumer no probado con schema inválido | Un evento malformado puede crashear el consumer en producción | Alta |
| I13: Contrato de eventos no validado | Cambio en `ticket-service` rompe los consumers silenciosamente | Alta |
| U33: `CreateUserUseCase` sin tests reales | Lógica de creación de usuarios sin cobertura | Alta |
| I9/I10: Tests de integración frágiles (requieren Docker) | No se pueden ejecutar en CI sin infraestructura completa | Media |
| S3: No hay E2E unificado entre los 3 servicios | El flujo completo del negocio no está probado end-to-end | Media |
| U16/U17: Transiciones de estado no cubiertas completamente | Posible bug de transición sin detectar | Baja |

---

## Justificación por Principio 6

| Nivel | Por qué este contexto lo exige |
|---|---|
| Unitario | El dominio es Python puro → tests rápidos, sin dependencias externas |
| Integración | La mensajería asíncrona no puede probarse a nivel unitario |
| Sistema | Solo 1 caso E2E: alto costo, bajo retorno más allá del happy path |

---

## Fase 3.1 — Técnicas de Diseño de Casos de Prueba (Nuevas Funcionalidades)

---

### Funcionalidad 1: Gestión manual de prioridad de tickets
> Fuente: [user-stories/USER_STORY_TICKET_PRIORITY.md](user-stories/USER_STORY_TICKET_PRIORITY.md)

#### Reglas de negocio

| Regla | Descripción |
|---|---|
| R1 | Solo el rol `Administrador` puede cambiar la prioridad |
| R2 | Solo se permite cambiar prioridad en tickets con estado `Open` o `In-Progress` |
| R3 | No se puede asignar `Unassigned` una vez que se ha asignado otra prioridad |
| R4 | La justificación es opcional; si se ingresa, debe mostrarse en el detalle |
| R5 | Los valores válidos de prioridad son: `Unassigned`, `Low`, `Medium`, `High` |

---

#### Técnica 1 — Partición de Equivalencia

Se agrupan las entradas en clases: una sola prueba por clase representa a todas las del grupo.

##### Variable: Rol del usuario

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP1 | `Administrador` | Válida | Cambio permitido (si otras condiciones OK) |
| EP2 | `Usuario` | Inválida | 🚫 Bloqueado: permiso insuficiente |

##### Variable: Estado del ticket

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP3 | `Open` | Válida | Cambio permitido (si otras condiciones OK) |
| EP4 | `In-Progress` | Válida | Cambio permitido (si otras condiciones OK) |
| EP5 | `Closed` | Inválida | 🚫 Bloqueado: estado no permitido |

##### Variable: Nueva prioridad destino

| Clase | Valores | Tipo | Condición adicional | Resultado esperado |
|---|---|---|---|---|
| EP6 | `Low`, `Medium`, `High` | Válida | — | Cambio exitoso |
| EP7 | `Unassigned` | Inválida | Prioridad actual ≠ `Unassigned` | 🚫 Bloqueado: no se puede volver a Unassigned |
| EP8 | `Unassigned` | Válida | Prioridad actual = `Unassigned` | No-op (ya tiene ese valor) |
| EP9 | Valor arbitrario (`"critical"`, `"urgent"`) | Inválida | — | 🚫 Rechazado: valor fuera de enumeración |

##### Variable: Justificación

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP10 | `None` / cadena vacía `""` | Válida | Cambio exitoso, sin sección de justificación en detalle |
| EP11 | Texto con contenido (`"Urgente por SLA"`) | Válida | Cambio exitoso, justificación visible en detalle del ticket |

---

#### Técnica 2 — Análisis de Valores Límite

##### Límite: Estados permitidos vs bloqueados

| Caso | Estado | Esperado |
|---|---|---|
| BVA1 | `Open` (primer estado permitido) | ✅ Cambio permitido |
| BVA2 | `In-Progress` (último estado permitido) | ✅ Cambio permitido |
| BVA3 | `Closed` (inmediatamente fuera del rango permitido) | 🚫 Bloqueado |

##### Límite: Transición de prioridad — borde Unassigned

| Caso | Prioridad actual | Prioridad destino | Esperado |
|---|---|---|---|
| BVA4 | `Unassigned` (primera asignación real a `Low`) | `Low` | ✅ Primer cambio permitido |
| BVA5 | `Low` (intento de retroceder al valor inicial) | `Unassigned` | 🚫 Bloqueado |
| BVA6 | `High` (cambio entre valores no-Unassigned) | `Low` | ✅ Permitido |

##### Límite: Longitud de la justificación

> ⚠️ **Pendiente de definición:** Las user stories no especifican longitud máxima para la justificación. Se propone un límite de **255 caracteres** (estándar de campo de texto corto en DB). Debe confirmarse con el equipo antes de implementar.

| Caso | Longitud del texto | Esperado |
|---|---|---|
| BVA7 | 0 caracteres (vacío) | ✅ Válido — justificación omitida |
| BVA8 | 254 caracteres (un carácter bajo el límite) | ✅ Válido |
| BVA9 | 255 caracteres (exactamente en el límite) | ✅ Válido |
| BVA10 | 256 caracteres (un carácter sobre el límite) | 🚫 Rechazado: excede longitud máxima |

---

#### Técnica 3 — Tabla de Decisión

Se aplica porque la lógica combina **tres condiciones independientes** que determinan si el cambio está permitido.

**Condiciones:**
- C1: ¿El usuario tiene rol `Administrador`?
- C2: ¿El ticket está en estado `Open` o `In-Progress`?
- C3: ¿La nueva prioridad es distinta de `Unassigned`?

**Acciones:**
- A1: Cambio de prioridad ejecutado ✅
- A2: Error — permiso insuficiente 🚫
- A3: Error — estado no válido 🚫
- A4: Error — no se puede volver a `Unassigned` 🚫

| Regla | C1: Admin | C2: Estado válido | C3: Destino ≠ Unassigned | Acción | Test |
|---|---|---|---|---|---|
| DT1 | No | Sí | Sí | A2 — permiso insuficiente | EP2 |
| DT2 | Sí | No | Sí | A3 — estado no válido | EP5, BVA3 |
| DT3 | Sí | Sí | Sí | A1 — cambio exitoso | EP1+EP3+EP6 |
| DT4 | Sí | Sí | No → origen ≠ Unassigned | A4 — no puede volver a Unassigned | BVA5, EP7 |
| DT5 | Sí | Sí | No → origen = Unassigned | No-op — sin cambio ni evento | EP8 |

##### Casos de prueba derivados

| # | Escenario concreto | Regla aplicada |
|---|---|---|
| DT-T1 | Usuario intenta cambiar prioridad de ticket Open a High | DT1 |
| DT-T2 | Admin intenta cambiar prioridad de ticket Closed | DT2 |
| DT-T3 | Admin cambia prioridad de ticket Open de Unassigned a High con justificación | DT3 |
| DT-T4 | Admin cambia prioridad de ticket In-Progress de Low a Medium sin justificación | DT3 |
| DT-T5 | Admin intenta cambiar prioridad de High a Unassigned | DT4 |
| DT-T6 | Admin cambia prioridad de Unassigned a Unassigned | DT5 |

---

### Funcionalidad 2: Respuestas de administrador y notificaciones en tiempo real
> Fuente: [user-stories/USER_STORY_NOTIFICATION.md](user-stories/USER_STORY_NOTIFICATION.md)

#### Reglas de negocio

| Regla | Descripción |
|---|---|
| R6 | Solo el rol `ADMIN` puede crear respuestas en tickets |
| R7 | Solo se puede responder tickets en estado `OPEN` o `IN_PROGRESS` |
| R8 | El texto de la respuesta es obligatorio, máximo 2000 caracteres |
| R9 | Cada respuesta genera el evento `ticket.response_added` |
| R10 | Las respuestas son visibles solo para el creador del ticket y usuarios ADMIN |
| R11 | La notificación es idempotente: un `response_id` duplicado no genera una segunda notificación |
| R12 | El canal SSE entrega la notificación al usuario creador del ticket en menos de 5 segundos |

---

#### Técnica 1 — Partición de Equivalencia

##### Variable: Rol del usuario (al crear respuesta)

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP12 | `ADMIN` | Válida | Respuesta creada, evento publicado |
| EP13 | `Usuario` | Inválida | 🚫 Bloqueado: permiso insuficiente |

##### Variable: Estado del ticket (al crear respuesta)

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP14 | `OPEN` | Válida | Respuesta permitida |
| EP15 | `IN_PROGRESS` | Válida | Respuesta permitida |
| EP16 | `CLOSED` | Inválida | 🚫 Bloqueado: no se puede responder ticket cerrado |

##### Variable: Texto de la respuesta

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP17 | Texto no vacío con longitud ≤ 2000 caracteres | Válida | Respuesta creada exitosamente |
| EP18 | Vacío / `None` | Inválida | 🚫 Rechazado: texto obligatorio |
| EP19 | Texto con longitud > 2000 caracteres | Inválida | 🚫 Rechazado: excede límite |

##### Variable: Idempotencia del evento (en Notification Service)

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP20 | `response_id` nuevo (primera vez) | Válida | Notificación creada |
| EP21 | `response_id` duplicado (ya procesado) | Inválida | No-op — no se crea notificación duplicada |

##### Variable: Estado de conexión SSE del usuario

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP22 | Usuario con conexión SSE activa | Válida | Recibe notificación en tiempo real (< 5 s) |
| EP23 | Usuario desconectado | Válida | Notificación persiste en DB y se entrega al reconectar |

##### Variable: Visibilidad de respuestas (al consultar)

| Clase | Valores | Tipo | Resultado esperado |
|---|---|---|---|
| EP24 | Creador del ticket consultando sus propias respuestas | Válida | Lista de respuestas visible |
| EP25 | ADMIN consultando respuestas de cualquier ticket | Válida | Lista de respuestas visible |
| EP26 | Usuario que NO es el creador intentando consultar | Inválida | 🚫 Denegado: acceso restringido |

---

#### Técnica 2 — Análisis de Valores Límite

##### Límite: Estados permitidos para responder

| Caso | Estado | Esperado |
|---|---|---|
| BVA11 | `OPEN` (primer estado permitido) | ✅ Respuesta permitida |
| BVA12 | `IN_PROGRESS` (último estado permitido) | ✅ Respuesta permitida |
| BVA13 | `CLOSED` (inmediatamente fuera del rango) | 🚫 Bloqueado |

##### Límite: Longitud del texto de respuesta

| Caso | Longitud del texto | Esperado |
|---|---|---|
| BVA14 | 0 caracteres (vacío) | 🚫 Inválido — texto obligatorio |
| BVA15 | 1 carácter (mínimo válido) | ✅ Válido |
| BVA16 | 1999 caracteres (un carácter bajo el límite) | ✅ Válido |
| BVA17 | 2000 caracteres (exactamente en el límite) | ✅ Válido |
| BVA18 | 2001 caracteres (un carácter sobre el límite) | 🚫 Rechazado: excede límite |

---

#### Técnica 3 — Tabla de Decisión

Se aplica a la creación de respuestas, que combina **tres condiciones** para determinar si la operación es válida.

**Condiciones:**
- C1: ¿El usuario tiene rol `ADMIN`?
- C2: ¿El ticket está en estado `OPEN` o `IN_PROGRESS`?
- C3: ¿El texto es no vacío y tiene ≤ 2000 caracteres?

**Acciones:**
- A1: Respuesta persistida y evento `ticket.response_added` publicado ✅
- A2: Error — permiso insuficiente 🚫
- A3: Error — estado no válido (ticket cerrado) 🚫
- A4: Error — texto inválido (vacío o demasiado largo) 🚫

| Regla | C1: Admin | C2: Estado válido | C3: Texto válido | Acción | Test |
|---|---|---|---|---|---|
| DT6 | No | Sí | Sí | A2 — permiso insuficiente | EP13 |
| DT7 | Sí | No | Sí | A3 — ticket cerrado | EP16, BVA13 |
| DT8 | Sí | Sí | No | A4 — texto inválido | EP18, EP19, BVA14, BVA18 |
| DT9 | Sí | Sí | Sí | A1 — respuesta creada y evento publicado | EP12+EP14+EP17 |

##### Casos de prueba derivados

| # | Escenario concreto | Regla aplicada |
|---|---|---|
| DT-T7 | Usuario intenta responder ticket OPEN | DT6 |
| DT-T8 | Admin intenta responder ticket CLOSED | DT7 |
| DT-T9 | Admin intenta enviar respuesta vacía en ticket OPEN | DT8 |
| DT-T10 | Admin intenta enviar respuesta de 2001 caracteres en ticket OPEN | DT8 |
| DT-T11 | Admin responde ticket OPEN con texto válido de 2000 caracteres | DT9 |
| DT-T12 | Admin responde ticket IN_PROGRESS con texto de 1 carácter | DT9 |
| DT-T13 | Notification Service recibe evento `ticket.response_added` duplicado → no crea segunda notificación | EP21 |
| DT-T14 | Usuario con SSE activa recibe notificación al ser respondido su ticket | EP22 |
| DT-T15 | Usuario desconectado acumula notificación y la recibe al reconectar | EP23 |

---

## Actividad 3.1 — Escenarios de Prueba en Formato Gherkin

> Generados a partir de los casos de prueba diseñados en las técnicas EP, BVA y DT de ambas funcionalidades.

---

### Funcionalidad 1: Gestión manual de prioridad de tickets

```gherkin
Feature: Gestión manual de prioridad de tickets por administrador

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Rol del usuario
  # ─────────────────────────────────────────────

  # EP1 — Clase válida: rol Administrador
  Scenario: Administrador cambia prioridad exitosamente (EP1, EP3, EP6)
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "High"
    Then la prioridad del ticket se actualiza a "High"

  # EP2 — Clase inválida: rol Usuario
  Scenario: Usuario sin permisos no puede cambiar prioridad (EP2)
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario autenticado tiene rol "Usuario"
    When intenta cambiar la prioridad a "High"
    Then el sistema bloquea la acción
    And se retorna un error de permiso insuficiente

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Estado del ticket
  # ─────────────────────────────────────────────

  # EP3 — Clase válida: estado Open
  Scenario: Cambio de prioridad permitido en ticket Open (EP3)
    Given un ticket en estado "Open"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "Medium"
    Then la prioridad del ticket se actualiza a "Medium"

  # EP4 — Clase válida: estado In-Progress
  Scenario: Cambio de prioridad permitido en ticket In-Progress (EP4)
    Given un ticket en estado "In-Progress" con prioridad "Low"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "High"
    Then la prioridad del ticket se actualiza a "High"

  # EP5 — Clase inválida: estado Closed
  Scenario: Cambio de prioridad bloqueado en ticket Closed (EP5)
    Given un ticket en estado "Closed"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "Low"
    Then el sistema bloquea la acción
    And se informa que solo es posible en estados "Open" o "In-Progress"

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Prioridad destino
  # ─────────────────────────────────────────────

  # EP6 — Clase válida: Low, Medium, High
  Scenario Outline: Cambio a prioridad válida es exitoso (EP6)
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "<prioridad>"
    Then la prioridad del ticket se actualiza a "<prioridad>"

    Examples:
      | prioridad |
      | Low       |
      | Medium    |
      | High      |

  # EP7 — Clase inválida: volver a Unassigned desde otro valor
  Scenario: No se puede volver a Unassigned una vez asignada prioridad (EP7)
    Given un ticket en estado "Open" con prioridad "Medium"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "Unassigned"
    Then el sistema bloquea la acción
    And se informa que no es posible volver a "Unassigned"

  # EP8 — Clase válida (no-op): prioridad actual ya es Unassigned
  Scenario: Asignar Unassigned a ticket que ya tiene Unassigned no genera cambio ni evento (EP8)
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "Unassigned"
    Then no se realiza ningún cambio
    And no se publica ningún evento de dominio

  # EP9 — Clase inválida: valor fuera de enumeración
  Scenario: Valor de prioridad fuera de enumeración es rechazado (EP9)
    Given un ticket en estado "Open"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "critical"
    Then el sistema rechaza la acción
    And se informa que el valor no es válido

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Justificación
  # ─────────────────────────────────────────────

  # EP10 — Clase válida: justificación vacía u omitida
  Scenario: Cambio de prioridad sin justificación es válido (EP10)
    Given un ticket en estado "In-Progress" con prioridad "Low"
    And el usuario autenticado tiene rol "Administrador"
    When cambia la prioridad a "High" sin ingresar justificación
    Then la prioridad del ticket se actualiza a "High"
    And no se muestra sección de justificación en el detalle

  # EP11 — Clase válida: justificación con contenido
  Scenario: Justificación ingresada se guarda y se muestra en el detalle (EP11)
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario autenticado tiene rol "Administrador"
    When cambia la prioridad a "High" con justificación "Urgente por SLA"
    Then la prioridad del ticket se actualiza a "High"
    And la justificación "Urgente por SLA" es visible en el detalle del ticket

  # ─────────────────────────────────────────────
  # ANÁLISIS DE VALORES LÍMITE — Borde Unassigned
  # ─────────────────────────────────────────────

  # BVA4 — Primera asignación real (Unassigned → Low)
  Scenario: Primera asignación de prioridad desde Unassigned es permitida (BVA4)
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario autenticado tiene rol "Administrador"
    When cambia la prioridad a "Low"
    Then la prioridad del ticket se actualiza a "Low"

  # BVA5 — Intento de retroceder a Unassigned
  Scenario: No se puede retroceder de Low a Unassigned (BVA5)
    Given un ticket en estado "Open" con prioridad "Low"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "Unassigned"
    Then el sistema bloquea la acción

  # BVA6 — Cambio entre valores no-Unassigned
  Scenario: Cambio entre prioridades válidas non-Unassigned es permitido (BVA6)
    Given un ticket en estado "Open" con prioridad "High"
    And el usuario autenticado tiene rol "Administrador"
    When cambia la prioridad a "Low"
    Then la prioridad del ticket se actualiza a "Low"

  # ─────────────────────────────────────────────
  # ANÁLISIS DE VALORES LÍMITE — Longitud justificación
  # ─────────────────────────────────────────────

  # BVA7 — 0 caracteres
  Scenario: Justificación vacía es aceptada (BVA7)
    Given un ticket en estado "Open"
    And el usuario autenticado tiene rol "Administrador"
    When cambia la prioridad a "High" con justificación de 0 caracteres
    Then la prioridad se actualiza exitosamente

  # BVA8/BVA9 — 254 y 255 caracteres (exactamente en el límite)
  Scenario Outline: Justificación dentro del límite de caracteres es aceptada (BVA8, BVA9)
    Given un ticket en estado "Open"
    And el usuario autenticado tiene rol "Administrador"
    When cambia la prioridad a "Medium" con una justificación de <longitud> caracteres
    Then la prioridad se actualiza exitosamente

    Examples:
      | longitud |
      | 254      |
      | 255      |

  # BVA10 — 256 caracteres (sobre el límite)
  Scenario: Justificación que excede el límite de caracteres es rechazada (BVA10)
    Given un ticket en estado "Open"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "Medium" con una justificación de 256 caracteres
    Then el sistema rechaza la acción
    And se informa que la justificación excede la longitud máxima

  # ─────────────────────────────────────────────
  # TABLA DE DECISIÓN
  # ─────────────────────────────────────────────

  # DT1 — Usuario sin rol Admin
  Scenario: Usuario no admin es bloqueado independientemente del estado y prioridad (DT1)
    Given un ticket en estado "Open" con prioridad "Low"
    And el usuario autenticado tiene rol "Usuario"
    When intenta cambiar la prioridad a "High"
    Then el sistema retorna error de permiso insuficiente

  # DT2 — Admin en estado no válido
  Scenario: Admin bloqueado en ticket Closed aunque la prioridad destino sea válida (DT2)
    Given un ticket en estado "Closed" con prioridad "Low"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "High"
    Then el sistema retorna error de estado no permitido

  # DT3 — Caso completamente válido con justificación
  Scenario: Admin cambia prioridad en ticket Open con justificación (DT3)
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario autenticado tiene rol "Administrador"
    When cambia la prioridad a "High" con justificación "Urgente por incidente"
    Then la prioridad del ticket se actualiza a "High"
    And la justificación queda registrada en el detalle del ticket

  # DT3 — Caso completamente válido sin justificación
  Scenario: Admin cambia prioridad en ticket In-Progress sin justificación (DT3)
    Given un ticket en estado "In-Progress" con prioridad "Low"
    And el usuario autenticado tiene rol "Administrador"
    When cambia la prioridad a "Medium" sin justificación
    Then la prioridad del ticket se actualiza a "Medium"

  # DT4 — Intento de volver a Unassigned
  Scenario: Admin no puede volver a Unassigned desde prioridad High (DT4)
    Given un ticket en estado "Open" con prioridad "High"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "Unassigned"
    Then el sistema retorna error indicando que no se puede volver a "Unassigned"

  # DT5 — No-op: prioridad ya es Unassigned
  Scenario: Asignar Unassigned a ticket que ya tiene Unassigned no genera cambio ni evento (DT5)
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario autenticado tiene rol "Administrador"
    When intenta cambiar la prioridad a "Unassigned"
    Then no se genera ningún cambio en la base de datos
    And no se publica ningún evento de dominio
```

---

### Funcionalidad 2: Respuestas de administrador y notificaciones en tiempo real

```gherkin
Feature: Respuestas de administrador en tickets

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Rol del usuario
  # ─────────────────────────────────────────────

  # EP12 — Clase válida: ADMIN
  Scenario: Admin crea respuesta en ticket OPEN exitosamente (EP12, EP14, EP17)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta con texto "Estamos revisando tu caso"
    Then la respuesta se persiste asociada al ticket
    And se publica el evento "ticket.response_added" en RabbitMQ

  # EP13 — Clase inválida: Usuario
  Scenario: Usuario sin permisos no puede crear respuesta (EP13)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "Usuario"
    When intenta enviar una respuesta con texto "Mi opinión"
    Then el sistema bloquea la acción
    And se retorna un error de permiso insuficiente

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Estado del ticket
  # ─────────────────────────────────────────────

  # EP14 — Clase válida: OPEN
  Scenario: Admin puede responder ticket en estado OPEN (EP14)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta válida
    Then la respuesta se crea exitosamente

  # EP15 — Clase válida: IN_PROGRESS
  Scenario: Admin puede responder ticket en estado IN_PROGRESS (EP15)
    Given un ticket en estado "IN_PROGRESS"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta válida
    Then la respuesta se crea exitosamente

  # EP16 — Clase inválida: CLOSED
  Scenario: Admin no puede responder ticket en estado CLOSED (EP16)
    Given un ticket en estado "CLOSED"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta
    Then el sistema bloquea la acción
    And se informa que no se pueden responder tickets cerrados

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Texto de la respuesta
  # ─────────────────────────────────────────────

  # EP17 — Clase válida: texto no vacío ≤ 2000 caracteres
  Scenario: Respuesta con texto válido se crea exitosamente (EP17)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta con texto "El problema ha sido identificado"
    Then la respuesta se persiste con el texto, el admin_id y la fecha de creación

  # EP18 — Clase inválida: vacío
  Scenario: Respuesta con texto vacío es rechazada (EP18)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta sin texto
    Then el sistema rechaza la acción
    And se informa que el texto es obligatorio

  # EP19 — Clase inválida: longitud > 2000
  Scenario: Respuesta que excede 2000 caracteres es rechazada (EP19)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta con 2001 caracteres
    Then el sistema rechaza la acción
    And se informa que el límite es 2000 caracteres

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Idempotencia
  # ─────────────────────────────────────────────

  # EP20 — Clase válida: response_id nuevo
  Scenario: Evento con response_id nuevo genera notificación (EP20)
    Given el Notification Service está consumiendo eventos de RabbitMQ
    And no existe ninguna notificación para el response_id "7"
    When se recibe evento "ticket.response_added" con response_id "7"
    Then se crea una notificación asociada al ticket

  # EP21 — Clase inválida: response_id duplicado
  Scenario: Evento duplicado con mismo response_id no genera segunda notificación (EP21)
    Given ya existe una notificación generada por el response_id "7"
    When se recibe nuevamente el evento con response_id "7"
    Then no se crea una notificación adicional

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Estado de conexión SSE
  # ─────────────────────────────────────────────

  # EP22 — Clase válida: usuario con SSE activa
  Scenario: Usuario conectado por SSE recibe notificación en menos de 5 segundos (EP22)
    Given el usuario "user-123" tiene una conexión SSE activa
    When un administrador responde su ticket
    Then el servidor envía un evento SSE con los datos de la notificación
    And el evento llega al navegador en menos de 5 segundos

  # EP23 — Clase válida: usuario desconectado
  Scenario: Usuario desconectado acumula notificación y la recibe al reconectar (EP23)
    Given el usuario "user-123" no tiene conexión SSE activa
    When un administrador responde su ticket
    Then la notificación se persiste en base de datos
    And cuando el usuario se reconecta recibe las notificaciones acumuladas

  # ─────────────────────────────────────────────
  # PARTICIÓN DE EQUIVALENCIA — Visibilidad de respuestas
  # ─────────────────────────────────────────────

  # EP24 — Clase válida: creador del ticket
  Scenario: Creador del ticket puede consultar las respuestas (EP24)
    Given un ticket creado por "user-123" con 2 respuestas
    And el usuario autenticado es "user-123" con rol "Usuario"
    When consulta las respuestas del ticket
    Then recibe las 2 respuestas en orden cronológico ascendente

  # EP25 — Clase válida: ADMIN
  Scenario: Admin puede consultar respuestas de cualquier ticket (EP25)
    Given un ticket creado por "user-456" con 1 respuesta
    And el usuario autenticado tiene rol "ADMIN"
    When consulta las respuestas del ticket
    Then recibe la respuesta correctamente

  # EP26 — Clase inválida: usuario que no es el creador
  Scenario: Usuario no creador no puede consultar las respuestas (EP26)
    Given un ticket creado por "user-789"
    And el usuario autenticado es "user-111" con rol "Usuario"
    When intenta consultar las respuestas del ticket
    Then el sistema deniega el acceso

  # ─────────────────────────────────────────────
  # ANÁLISIS DE VALORES LÍMITE — Estado del ticket
  # ─────────────────────────────────────────────

  # BVA11 — OPEN (primer estado permitido)
  Scenario: Respuesta en ticket OPEN es el primer borde permitido (BVA11)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta válida
    Then la respuesta se crea exitosamente

  # BVA12 — IN_PROGRESS (último estado permitido)
  Scenario: Respuesta en ticket IN_PROGRESS es el último borde permitido (BVA12)
    Given un ticket en estado "IN_PROGRESS"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta válida
    Then la respuesta se crea exitosamente

  # BVA13 — CLOSED (fuera del rango permitido)
  Scenario: Respuesta en ticket CLOSED está fuera del rango permitido (BVA13)
    Given un ticket en estado "CLOSED"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta
    Then el sistema bloquea la acción

  # ─────────────────────────────────────────────
  # ANÁLISIS DE VALORES LÍMITE — Longitud del texto
  # ─────────────────────────────────────────────

  # BVA14 — 0 caracteres (inválido)
  Scenario: Respuesta vacía es inválida (BVA14)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta de 0 caracteres
    Then el sistema rechaza la acción
    And se informa que el texto es obligatorio

  # BVA15 — 1 carácter (mínimo válido)
  Scenario: Respuesta de 1 carácter es el mínimo válido (BVA15)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta de 1 carácter
    Then la respuesta se crea exitosamente

  # BVA16 — 1999 caracteres (bajo el límite)
  Scenario: Respuesta de 1999 caracteres es válida (BVA16)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta de 1999 caracteres
    Then la respuesta se crea exitosamente

  # BVA17 — 2000 caracteres (exactamente en el límite)
  Scenario: Respuesta de exactamente 2000 caracteres es válida (BVA17)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta de exactamente 2000 caracteres
    Then la respuesta se crea exitosamente

  # BVA18 — 2001 caracteres (sobre el límite)
  Scenario: Respuesta de 2001 caracteres excede el límite y es rechazada (BVA18)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta de 2001 caracteres
    Then el sistema rechaza la acción
    And se informa que el límite máximo es 2000 caracteres

  # ─────────────────────────────────────────────
  # TABLA DE DECISIÓN
  # ─────────────────────────────────────────────

  # DT6 — Usuario sin permisos
  Scenario: Usuario bloqueado independientemente del estado y texto (DT6)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "Usuario"
    When intenta enviar una respuesta con texto válido
    Then el sistema retorna error de permiso insuficiente

  # DT7 — Admin en ticket CLOSED
  Scenario: Admin bloqueado en ticket CLOSED aunque el texto sea válido (DT7)
    Given un ticket en estado "CLOSED"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta con texto válido
    Then el sistema retorna error de ticket cerrado

  # DT8 — Admin, estado válido, pero texto inválido
  Scenario: Admin con texto vacío es rechazado aunque el estado sea válido (DT8)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta vacía
    Then el sistema retorna error de texto obligatorio

  Scenario: Admin con texto de 2001 caracteres es rechazado aunque el estado sea válido (DT8)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta de 2001 caracteres
    Then el sistema retorna error de límite de caracteres excedido

  # DT9 — Caso completamente válido
  Scenario: Admin responde ticket OPEN con texto de exactamente 2000 caracteres (DT9)
    Given un ticket en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta de exactamente 2000 caracteres
    Then la respuesta se persiste en la base de datos
    And se publica el evento "ticket.response_added" con todos los campos requeridos

  Scenario: Admin responde ticket IN_PROGRESS con texto de 1 carácter (DT9)
    Given un ticket en estado "IN_PROGRESS"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta de 1 carácter
    Then la respuesta se persiste en la base de datos
    And se publica el evento "ticket.response_added"
```

---
