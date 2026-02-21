# Especificación Funcional: Respuestas de Admin + Notificaciones en Tiempo Real

**Proyecto:** Sistema de Tickets — Arquitectura de Microservicios  
**Fecha:** Febrero 2026  
**Elaborado por:** IRIS (Intelligent Requirements & Insight Synthesizer)  
**Estado:** Especificación definitiva — Todos los TBD resueltos

---

## 1. Contexto MVP

El sistema actual de tickets permite crear tickets, cambiar estados y generar notificaciones al crear un ticket. No existe capacidad para que un administrador responda tickets, ni mecanismo de notificación en tiempo real hacia el usuario.

Esta especificación define tres capacidades nuevas:
1. Respuestas de administrador en tickets
2. Notificaciones en tiempo real vía SSE
3. Visualización de respuestas y formulario en el frontend

### Decisiones MVP Confirmadas

| Decisión                       | Resolución MVP                                                    |
| ------------------------------ | ----------------------------------------------------------------- |
| Permisos de respuesta          | Solo usuarios con rol ADMIN pueden responder                      |
| Dirección de comunicación      | Unidireccional (Admin → Usuario)                                  |
| Responder tickets CLOSED       | No permitido (consistente con regla TicketAlreadyClosed)          |
| Mecanismo de tiempo real       | SSE (Server-Sent Events) — sin WebSockets ni Django Channels      |
| Visibilidad de respuestas      | Solo el creador del ticket y usuarios ADMIN                       |
| Contenido de notificación      | Resumen corto + link al detalle del ticket                        |
| Notificaciones por email       | No en MVP — solo in-app                                           |
| Límite de caracteres           | Máximo 2000 caracteres por respuesta                              |

---

## 2. Objetivos de Negocio

1. **Permitir a administradores responder tickets** — Comunicación centralizada dentro del sistema
2. **Notificar al usuario creador en tiempo real vía SSE** — Sin recargar la página, latencia < 5 segundos
3. **Visualizar respuestas en el detalle del ticket** — Historial cronológico completo, visible solo para creador y admins

---

## 3. Capacidades Técnicas

| #   | Capacidad                                                    | Servicio impactado                | Detalle                                                                                               |
| --- | ------------------------------------------------------------ | --------------------------------- | ----------------------------------------------------------------------------------------------------- |
| C1  | Crear respuesta asociada a un ticket                         | **Ticket Service**                | Nueva entidad de dominio Response (texto, admin_id, ticket_id, timestamp). Máximo 2000 caracteres     |
| C2  | Validar permisos: solo ADMIN                                 | **Ticket Service**                | Regla de dominio + validación en presentación                                                         |
| C3  | Validar estado: solo OPEN o IN_PROGRESS                      | **Ticket Service**                | Regla de dominio — reutilizar patrón TicketAlreadyClosed                                              |
| C4  | Consultar respuestas por ticket                              | **Ticket Service**                | Endpoint REST. Filtrar por visibilidad: solo creador del ticket y admins                               |
| C5  | Publicar evento ticket.response_added                        | **Ticket Service** → RabbitMQ     | Incluye user_id (creador) para que Notification Service sepa a quién notificar                        |
| C6  | Consumir evento y crear notificación                         | **Notification Service**          | Nuevo handler, idempotente por response_id                                                            |
| C7  | Canal SSE para entregar notificaciones en tiempo real        | **Notification Service**          | Endpoint SSE que emite eventos al usuario conectado                                                   |
| C8  | Conexión SSE en el frontend                                  | **Frontend**                      | EventSource API, reconexión automática                                                                |
| C9  | Mostrar respuestas en detalle de ticket                      | **Frontend**                      | Nueva sección en TicketDetail, orden cronológico ascendente                                           |
| C10 | Formulario de respuesta (solo ADMIN)                         | **Frontend**                      | Visible solo si role === ADMIN y ticket no CLOSED. Textarea con límite 2000 chars                     |

---

## 4. Épicas

### Épica 1: Respuestas de Administrador en Tickets

**Objetivo:** Permitir que administradores respondan tickets con texto (máximo 2000 caracteres), persistiendo la respuesta y publicando un evento de dominio.

**Reglas de negocio:**
- Solo usuarios con rol ADMIN pueden crear respuestas
- Solo en tickets con estado OPEN o IN_PROGRESS
- Texto obligatorio, máximo 2000 caracteres
- Cada respuesta genera evento ticket.response_added
- Respuestas visibles solo para el creador del ticket y usuarios ADMIN

### Épica 2: Notificaciones en Tiempo Real (SSE)

**Objetivo:** Cuando un administrador responde un ticket, el usuario creador recibe una notificación in-app en tiempo real mediante Server-Sent Events.

**Reglas:**
- Mecanismo: SSE (Server-Sent Events) — sin WebSockets ni Django Channels
- Solo in-app, sin email
- Notificación con resumen corto + link al detalle del ticket
- Idempotencia: si el evento se recibe duplicado, no se crea notificación repetida
- Notificaciones pendientes se acumulan si el usuario está desconectado

### Épica 3: Visualización de Respuestas y Formulario en Frontend

**Objetivo:** El usuario ve las respuestas del admin en el detalle del ticket. El admin, además, dispone de un formulario para responder directamente.

**Reglas:**
- Formulario visible solo para ADMIN y tickets no CLOSED
- Usuario con rol USER ve las respuestas en modo lectura (solo sus propios tickets)
- Orden cronológico ascendente
- Textarea con contador de caracteres y límite visual a 2000

---

## 5. Historias de Usuario

### HU-1.1: Crear respuesta en un ticket

**Como** administrador  
**quiero** escribir una respuesta de texto en un ticket en estado OPEN o IN_PROGRESS  
**para** comunicar al usuario creador la resolución o avance de su solicitud

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:respuestas-admin @story:HU-1.1 @priority:alta
Feature: Crear respuesta de administrador en un ticket
  Como administrador
  Quiero escribir una respuesta en un ticket
  Para comunicar al usuario la resolución o avance de su solicitud

  Background:
    Given un ticket existente en el sistema con un usuario creador

  Scenario: Admin responde ticket en estado OPEN
    Given el ticket está en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta con texto "Estamos revisando tu caso"
    Then la respuesta se persiste asociada al ticket
    And la respuesta contiene el texto, el ID del admin y la fecha de creación
    And se publica el evento "ticket.response_added" en RabbitMQ

  Scenario: Admin responde ticket en estado IN_PROGRESS
    Given el ticket está en estado "IN_PROGRESS"
    And el usuario autenticado tiene rol "ADMIN"
    When envía una respuesta con texto "El problema ha sido identificado"
    Then la respuesta se persiste asociada al ticket
    And se publica el evento "ticket.response_added" en RabbitMQ

  Scenario: Admin intenta responder ticket CLOSED
    Given el ticket está en estado "CLOSED"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta
    Then el sistema rechaza la acción
    And retorna un error indicando que no se pueden responder tickets cerrados

  Scenario: Respuesta con texto vacío
    Given el ticket está en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta sin texto
    Then el sistema rechaza la acción
    And retorna un error indicando que el texto es obligatorio

  Scenario: Respuesta excede 2000 caracteres
    Given el ticket está en estado "OPEN"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta con 2001 caracteres
    Then el sistema rechaza la acción
    And retorna un error indicando que el límite es 2000 caracteres

  Scenario: Usuario con rol USER intenta responder
    Given el ticket está en estado "OPEN"
    And el usuario autenticado tiene rol "USER"
    When intenta enviar una respuesta
    Then el sistema rechaza la acción
    And retorna un error de permiso insuficiente

  Scenario Outline: Validación de estados permitidos para responder
    Given el ticket está en estado "<estado>"
    And el usuario autenticado tiene rol "ADMIN"
    When intenta enviar una respuesta con texto válido
    Then el resultado es "<resultado>"

    Examples:
      | estado      | resultado                         |
      | OPEN        | Respuesta creada exitosamente     |
      | IN_PROGRESS | Respuesta creada exitosamente     |
      | CLOSED      | Error: ticket cerrado             |
```

**Notas:**
- Valor: Centraliza la comunicación admin→usuario dentro del sistema
- Dependencias: Ticket Service (dominio, aplicación, infraestructura), RabbitMQ

---

### HU-1.2: Consultar respuestas de un ticket (con control de visibilidad)

**Como** usuario del sistema  
**quiero** ver todas las respuestas de un ticket  
**para** conocer el historial de comunicación sobre la solicitud

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:respuestas-admin @story:HU-1.2 @priority:alta
Feature: Consultar respuestas de un ticket con control de visibilidad
  Como usuario del sistema
  Quiero ver las respuestas de un ticket
  Para conocer el historial de comunicación

  Scenario: Creador del ticket consulta respuestas
    Given un ticket creado por el usuario "user-123" con 3 respuestas
    And el usuario autenticado es "user-123" con rol "USER"
    When consulta las respuestas del ticket
    Then recibe las 3 respuestas en orden cronológico ascendente
    And cada respuesta incluye texto, nombre del admin que respondió y fecha

  Scenario: Admin consulta respuestas de cualquier ticket
    Given un ticket creado por "user-456" con 2 respuestas
    And el usuario autenticado tiene rol "ADMIN"
    When consulta las respuestas del ticket
    Then recibe las 2 respuestas en orden cronológico ascendente

  Scenario: Usuario que no es el creador intenta consultar respuestas
    Given un ticket creado por "user-789"
    And el usuario autenticado es "user-111" con rol "USER"
    When intenta consultar las respuestas del ticket
    Then el sistema rechaza la acción
    And retorna un error de acceso denegado

  Scenario: Ticket sin respuestas
    Given un ticket sin respuestas
    And el usuario autenticado es el creador del ticket
    When consulta las respuestas
    Then recibe una lista vacía
```

**Notas:**
- Valor: Trazabilidad de la comunicación respetando privacidad
- Regla de visibilidad: Solo el user_id creador del ticket y cualquier ADMIN pueden ver las respuestas

---

### HU-2.1: Generar notificación al responder un ticket

**Como** sistema  
**quiero** crear una notificación cuando un administrador responde un ticket  
**para** que el usuario creador sea informado del avance

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:notificaciones-sse @story:HU-2.1 @priority:alta
Feature: Generar notificación al recibir evento ticket.response_added
  Como sistema
  Quiero crear una notificación cuando se recibe el evento ticket.response_added
  Para informar al creador del ticket

  Background:
    Given el Notification Service está consumiendo eventos de RabbitMQ

  Scenario: Evento ticket.response_added genera notificación
    Given se publica un evento "ticket.response_added" con los datos:
      | campo          | valor                        |
      | ticket_id      | 42                           |
      | response_id    | 7                            |
      | admin_id       | admin-001                    |
      | response_text  | Estamos revisando tu caso    |
      | user_id        | user-123                     |
    When el Notification Service consume el evento
    Then se crea una notificación con mensaje "Nueva respuesta en Ticket #42"
    And la notificación se asocia al ticket_id "42"
    And la notificación se marca como no leída

  Scenario: Evento duplicado no genera notificación duplicada
    Given ya existe una notificación generada por response_id "7"
    When se recibe nuevamente el evento con response_id "7"
    Then no se crea una notificación adicional

  Scenario: Evento con formato inválido se descarta
    Given se recibe un evento "ticket.response_added" sin campo "ticket_id"
    When el Notification Service intenta procesarlo
    Then el evento se descarta
    And se registra un error estructurado en el log
```

**Notas:**
- Valor: Sin esta pieza, el usuario no se entera de nuevas respuestas
- Idempotencia: Se usa response_id como clave de deduplicación

---

### HU-2.2: Entregar notificaciones en tiempo real vía SSE

**Como** usuario con rol USER  
**quiero** recibir notificaciones en mi navegador sin recargar la página  
**para** enterarme inmediatamente cuando el administrador responde mi ticket

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:notificaciones-sse @story:HU-2.2 @priority:alta
Feature: Notificaciones en tiempo real vía Server-Sent Events
  Como usuario normal
  Quiero recibir notificaciones sin recargar la página
  Para enterarme inmediatamente de las respuestas

  Scenario: Usuario conectado recibe notificación en tiempo real
    Given el usuario "user-123" está autenticado
    And tiene una conexión SSE activa al endpoint de notificaciones
    When un administrador responde su ticket
    Then el servidor envía un evento SSE con los datos de la notificación
    And el evento llega al navegador en menos de 5 segundos
    And el contador de notificaciones no leídas se incrementa

  Scenario: Reconexión automática tras pérdida de conexión
    Given el usuario tiene una conexión SSE activa
    When la conexión se interrumpe temporalmente
    Then el navegador reconecta automáticamente usando EventSource
    And las notificaciones generadas durante la desconexión se recuperan al reconectar

  Scenario: Usuario desconectado acumula notificaciones
    Given el usuario "user-123" no tiene conexión SSE activa
    When un administrador responde su ticket
    Then la notificación se persiste en base de datos
    And cuando el usuario vuelve a conectarse, ve las notificaciones acumuladas

  Scenario: Solo se envían notificaciones al usuario correspondiente
    Given los usuarios "user-123" y "user-456" tienen conexiones SSE activas
    When un administrador responde un ticket creado por "user-123"
    Then solo "user-123" recibe el evento SSE
    And "user-456" no recibe ningún evento
```

**Notas:**
- Valor: Latencia mínima sin la complejidad de WebSockets
- Técnico: SSE usa HTTP estándar, reconexión nativa del navegador, compatible con la infraestructura actual

---

### HU-3.1: Ver respuestas en el detalle del ticket

**Como** usuario (creador del ticket o ADMIN)  
**quiero** ver las respuestas del administrador en la página de detalle del ticket  
**para** leer la comunicación completa sobre la solicitud

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:visualizacion-respuestas @story:HU-3.1 @priority:alta
Feature: Visualizar respuestas en el detalle del ticket
  Como usuario del sistema
  Quiero ver las respuestas en la pantalla de detalle del ticket
  Para leer el historial completo de comunicación

  Scenario: Detalle muestra respuestas existentes
    Given un ticket con 2 respuestas de administradores
    And el usuario autenticado es el creador del ticket
    When navega al detalle del ticket
    Then se muestra una sección "Respuestas" con las 2 respuestas
    And cada respuesta muestra el nombre del admin, la fecha y el texto completo
    And las respuestas están en orden cronológico ascendente (más antigua primero)

  Scenario: Detalle sin respuestas
    Given un ticket sin respuestas
    And el usuario autenticado es el creador del ticket
    When navega al detalle del ticket
    Then se muestra un mensaje "Aún no hay respuestas para este ticket"

  Scenario: Nueva respuesta aparece automáticamente
    Given el usuario está viendo el detalle de su ticket
    And tiene conexión SSE activa
    When un administrador envía una nueva respuesta a ese ticket
    Then la respuesta aparece automáticamente en la sección de respuestas
    But no es necesario recargar la página

  Scenario: Usuario no creador no puede ver el detalle con respuestas
    Given un ticket creado por "user-789"
    And el usuario autenticado es "user-111" con rol "USER"
    When intenta navegar al detalle del ticket
    Then no se muestran las respuestas
    And se muestra un mensaje de acceso restringido
```

**Notas:**
- Valor: Transforma el TicketDetail de placeholder a vista funcional con historial completo

---

### HU-3.2: Formulario de respuesta para administrador

**Como** administrador  
**quiero** un formulario de respuesta en el detalle del ticket  
**para** escribir y enviar mi respuesta directamente desde la interfaz

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:visualizacion-respuestas @story:HU-3.2 @priority:alta
Feature: Formulario de respuesta en detalle del ticket (solo ADMIN)
  Como administrador
  Quiero un formulario en el detalle del ticket
  Para escribir y enviar mi respuesta directamente

  Background:
    Given el usuario está autenticado

  Scenario: Admin ve formulario en ticket OPEN
    Given el usuario tiene rol "ADMIN"
    And el ticket está en estado "OPEN"
    When navega al detalle del ticket
    Then se muestra un textarea con placeholder "Escribe tu respuesta..."
    And un botón "Responder"
    And un contador de caracteres "0 / 2000"

  Scenario: Admin ve formulario en ticket IN_PROGRESS
    Given el usuario tiene rol "ADMIN"
    And el ticket está en estado "IN_PROGRESS"
    When navega al detalle del ticket
    Then se muestra el formulario de respuesta

  Scenario: Usuario con rol USER no ve formulario
    Given el usuario tiene rol "USER"
    When navega al detalle de su ticket
    Then no se muestra el formulario de respuesta
    And solo ve las respuestas en modo lectura

  Scenario: Formulario deshabilitado en ticket CLOSED
    Given el usuario tiene rol "ADMIN"
    And el ticket está en estado "CLOSED"
    When navega al detalle del ticket
    Then el formulario no está disponible
    And se muestra un aviso "Este ticket está cerrado. No se pueden agregar respuestas"

  Scenario: Admin envía respuesta exitosamente
    Given el usuario tiene rol "ADMIN"
    And el ticket está en estado "IN_PROGRESS"
    When escribe "Tu problema fue resuelto" y presiona "Responder"
    Then la respuesta aparece inmediatamente en la lista de respuestas
    And el textarea se limpia
    And el contador vuelve a "0 / 2000"
    And se muestra una confirmación temporal de éxito

  Scenario: Contador de caracteres alcanza el límite
    Given el usuario tiene rol "ADMIN"
    And el formulario está visible
    When escribe texto que alcanza los 2000 caracteres
    Then el contador muestra "2000 / 2000" en color de advertencia
    And no se permite escribir más caracteres

  Scenario: Botón deshabilitado con textarea vacío
    Given el usuario tiene rol "ADMIN"
    And el formulario está visible
    When el textarea está vacío
    Then el botón "Responder" está deshabilitado
```

**Notas:**
- Valor: Experiencia fluida para el admin, sin salir del contexto del ticket

---

## 6. Contratos de Eventos

### 6.1 Evento RabbitMQ: ticket.response_added

```json
{
  "event_type": "ticket.response_added",
  "ticket_id": 42,
  "response_id": 7,
  "admin_id": "admin-001",
  "response_text": "Estamos revisando tu caso",
  "user_id": "user-123",
  "timestamp": "2026-02-18T14:30:00Z"
}
```

| Campo           | Tipo             | Obligatorio | Descripción                                                        |
| --------------- | ---------------- | ----------- | ------------------------------------------------------------------ |
| event_type      | string           | Sí          | Siempre "ticket.response_added"                                    |
| ticket_id       | int              | Sí          | ID del ticket respondido                                           |
| response_id     | int              | Sí          | ID único de la respuesta (clave de idempotencia)                   |
| admin_id        | string           | Sí          | ID del administrador que respondió                                 |
| response_text   | string           | Sí          | Texto de la respuesta (máx 2000 chars)                             |
| user_id         | string           | Sí          | ID del creador del ticket (destinatario de la notificación)        |
| timestamp       | string (ISO8601) | Sí          | Fecha y hora de creación de la respuesta                           |

### 6.2 Evento SSE (Frontend)

```
event: notification
data: {"id": "notif-99", "ticket_id": 42, "message": "Nueva respuesta en Ticket #42", "created_at": "2026-02-18T14:30:01Z"}
```

---

## 7. Journey: Admin Responde → Usuario Notificado en Tiempo Real

```
 ADMIN                          SISTEMA                           USER
  │                                │                                │
  │  1. Navega al detalle          │                                │
  │     del ticket #42             │                                │
  │                                │                                │
  │  2. Escribe respuesta          │                                │
  │     en el formulario           │                                │
  │     (máx 2000 chars)           │                                │
  │                                │                                │
  │  3. Presiona "Responder"       │                                │
  │ ──────────────────────────────>│                                │
  │                                │  4. Ticket Service:            │
  │                                │     - Valida rol ADMIN         │
  │                                │     - Valida estado ≠ CLOSED   │
  │                                │     - Valida texto ≤ 2000      │
  │                                │     - Persiste Response        │
  │                                │     - Publica evento           │
  │                                │       ticket.response_added    │
  │  5. Respuesta aparece          │                                │
  │     en la lista                │                                │
  │<───────────────────────────────│                                │
  │                                │  6. Notification Service:      │
  │                                │     - Consume evento           │
  │                                │     - Deduplica por            │
  │                                │       response_id              │
  │                                │     - Crea notificación        │
  │                                │     - Emite evento SSE         │
  │                                │       al user_id               │
  │                                │ ──────────────────────────────>│
  │                                │                                │  7. Indicador visual
  │                                │                                │     de nueva notificación
  │                                │                                │
  │                                │                                │  8. Abre notificaciones
  │                                │                                │     → "Nueva respuesta
  │                                │                                │        en Ticket #42"
  │                                │                                │
  │                                │                                │  9. Navega al detalle
  │                                │                                │     del ticket #42
  │                                │                                │
  │                                │                                │  10. Lee la respuesta
  │                                │                                │      del admin
```

---

## 8. Resumen de Backlog por Prioridad

| Historia | Épica                    | Prioridad | Complejidad estimada                       |
| -------- | ------------------------ | --------- | ------------------------------------------ |
| HU-1.1   | Respuestas Admin         | Alta      | Media-Alta (dominio + evento + API)        |
| HU-1.2   | Respuestas Admin         | Alta      | Media (endpoint + filtro de acceso)        |
| HU-2.1   | Notificaciones SSE       | Alta      | Media (handler + idempotencia)             |
| HU-2.2   | Notificaciones SSE       | Alta      | Alta (canal SSE backend + frontend)        |
| HU-3.1   | Frontend Respuestas      | Alta      | Media (componente React + API)             |
| HU-3.2   | Frontend Respuestas      | Alta      | Media (componente React + validaciones)    |

### Orden de implementación sugerido

1. **HU-1.1** → **HU-1.2** — Backend primero: modelo de dominio, API REST, evento
2. **HU-2.1** — Notification handler para el nuevo evento
3. **HU-3.1** → **HU-3.2** — Frontend: detalle del ticket + formulario admin
4. **HU-2.2** — SSE: endpoint backend + EventSource frontend (integra todo)
