# Especificación Funcional: Gestión Manual de Prioridad por Administrador

**Proyecto:** Sistema de Tickets — Arquitectura de Microservicios  
**Fecha:** Febrero 2026  
**Elaborado por:** IRIS (Intelligent Requirements & Insight Synthesizer)  
**Estado:** Especificación definitiva

---

## 1. Contexto MVP

El sistema actualmente asigna prioridad de forma automática y aleatoria. Se requiere que el administrador defina manualmente la prioridad en el panel, con valores `Unassigned` (por defecto), `Low`, `Medium` y `High`. No habrá auditoría, trazabilidad ni historial. No se envían notificaciones. La justificación es opcional, pero si se ingresa debe mostrarse en el detalle del ticket. No se permite volver a `Unassigned` después de haber asignado una prioridad.

### Decisiones MVP Confirmadas

| Decisión                                    | Resolución MVP                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------------ |
| Valores de prioridad                        | `Unassigned` (por defecto), `Low`, `Medium`, `High`                            |
| Permisos de asignación                      | Solo usuarios con rol Administrador pueden asignar prioridad                   |
| Estados permitidos para cambio              | Solo `Open` o `In-Progress`                                                    |
| Reversión a Unassigned                      | No permitida una vez asignada otra prioridad                                   |
| Auditoría / historial de cambios            | No en MVP                                                                      |
| Notificaciones al cambiar prioridad         | No en MVP                                                                      |
| Justificación del cambio                    | Opcional — si se ingresa, se muestra en el detalle del ticket                  |

---

## 2. Objetivos de Negocio

1. **Permitir a administradores asignar prioridad manualmente** — Eliminar la asignación aleatoria actual
2. **Restringir cambios por rol y estado del ticket** — Solo admins en tickets `Open` o `In-Progress`
3. **Mostrar la justificación cuando se ingrese** — Visibilidad del motivo del cambio en el detalle
4. **Bloquear la reversión a Unassigned** — Evitar pérdida de información de prioridad ya asignada

---

## 3. Capacidades Técnicas

| #   | Capacidad                                                          | Servicio impactado | Detalle                                                                                        |
| --- | ------------------------------------------------------------------ | ------------------ | ---------------------------------------------------------------------------------------------- |
| C1  | Mostrar prioridad actual en listado y detalle                      | **Ticket Service** | Incluye valor `Unassigned` por defecto si no hay prioridad asignada                            |
| C2  | Permitir cambiar prioridad a `Low`, `Medium` o `High`              | **Ticket Service** | Regla de dominio + validación en presentación                                                  |
| C3  | Bloquear asignación a `Unassigned` si ya hay prioridad definida    | **Ticket Service** | Regla de dominio — excepción si se intenta revertir                                            |
| C4  | Validar rol Administrador                                          | **Ticket Service** | Solo usuarios con rol `ADMIN` pueden ejecutar el cambio                                        |
| C5  | Validar estado del ticket permitido para cambio                    | **Ticket Service** | Solo `OPEN` o `IN_PROGRESS` — rechazar si `CLOSED`                                            |
| C6  | Capturar justificación opcional y mostrarla en el detalle          | **Frontend**       | Campo de texto libre, no obligatorio. Si existe, se renderiza en la vista de detalle del ticket |

---

## 4. Épicas

### Épica 1: Gestión de Prioridad por Administradores

**Objetivo:** Permitir que los administradores asignen y modifiquen manualmente la prioridad de un ticket, reemplazando la lógica aleatoria actual, con restricciones de rol, estado y reversión.

**Reglas de negocio:**
- Solo usuarios con rol Administrador pueden cambiar la prioridad
- Solo en tickets con estado `OPEN` o `IN_PROGRESS`
- No se permite volver a `Unassigned` una vez asignada otra prioridad
- La justificación es opcional; si se provee, se persiste y muestra en el detalle
- No se generan notificaciones ni se registra historial de cambios

---

## 5. Historias de Usuario

### HU-1.1: Asignar prioridad a un ticket

**Como** administrador  
**quiero** cambiar la prioridad de un ticket en estado `Open` o `In-Progress`  
**para** reflejar su urgencia real

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:gestion-prioridad @story:HU-1.1 @priority:alta
Feature: Cambiar prioridad de ticket por administrador
  Como administrador
  Quiero cambiar la prioridad de un ticket
  Para reflejar su urgencia real

  Scenario: Administrador asigna prioridad en ticket Open
    Given un ticket en estado "Open" con prioridad "Unassigned"
    And el usuario tiene rol "Administrador"
    When selecciona la prioridad "High" y confirma el cambio
    Then la prioridad del ticket se actualiza a "High"

  Scenario: Administrador asigna prioridad en ticket In-Progress
    Given un ticket en estado "In-Progress" con prioridad "Low"
    And el usuario tiene rol "Administrador"
    When selecciona la prioridad "Medium" y confirma el cambio
    Then la prioridad del ticket se actualiza a "Medium"
```

**Notas:**
- Valor: Reemplaza la asignación aleatoria por una decisión deliberada del administrador
- Dependencias: Ticket Service (dominio, aplicación, infraestructura), Frontend (panel admin)

---

### HU-1.2: Visualizar prioridad en listado y detalle

**Como** administrador  
**quiero** ver la prioridad actual en el listado y en el detalle del ticket  
**para** decidir cambios sin pasos adicionales

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:gestion-prioridad @story:HU-1.2 @priority:alta
Feature: Visualizar prioridad del ticket
  Como administrador
  Quiero ver la prioridad actual del ticket
  Para decidir cambios sin pasos adicionales

  Scenario: Prioridad visible en listado
    Given el listado de tickets del panel administrador
    When se renderiza la vista
    Then cada ticket muestra su prioridad actual
    And si no hay prioridad asignada se muestra "Unassigned"

  Scenario: Prioridad visible en detalle
    Given el detalle de un ticket
    When se renderiza la vista
    Then se muestra la prioridad actual del ticket
```

**Notas:**
- Valor: Visibilidad inmediata del estado de prioridad sin requerir navegación adicional
- Dependencias: Frontend (componentes de listado y detalle), Ticket Service (API)

---

### HU-1.3: Justificación opcional en cambio de prioridad

**Como** administrador  
**quiero** que la justificación sea opcional al cambiar la prioridad  
**para** no bloquear cambios urgentes que requieren rapidez

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:gestion-prioridad @story:HU-1.3 @priority:media
Feature: Justificación opcional en cambio de prioridad
  Como administrador
  Quiero que la justificación sea opcional al cambiar prioridad
  Para no bloquear cambios urgentes

  Scenario: Cambio con justificación
    Given un ticket en estado "Open"
    And el usuario tiene rol "Administrador"
    When selecciona la prioridad "High" e ingresa una justificación
    And confirma el cambio
    Then la prioridad se actualiza
    And la justificación se guarda

  Scenario: Cambio sin justificación
    Given un ticket en estado "In-Progress"
    And el usuario tiene rol "Administrador"
    When selecciona la prioridad "Low" sin ingresar justificación
    And confirma el cambio
    Then la prioridad se actualiza
```

**Notas:**
- Valor: Flexibilidad operativa — no impone fricción en casos urgentes
- Dependencias: Ticket Service (persistencia del campo), Frontend (campo de texto opcional)

---

### HU-1.4: Restricciones por rol, estado y reversión a Unassigned

**Como** administrador  
**quiero** que el sistema bloquee cambios de prioridad inválidos  
**para** asegurar el control de permisos y la integridad del proceso

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:gestion-prioridad @story:HU-1.4 @priority:alta
Feature: Restricciones por rol, estado y prioridad
  Como administrador
  Quiero que el sistema bloquee cambios inválidos de prioridad
  Para asegurar el control de permisos y el proceso

  Scenario: Usuario sin rol Administrador intenta cambiar prioridad
    Given un ticket en estado "Open"
    And el usuario tiene rol "Usuario"
    When intenta cambiar la prioridad
    Then el sistema bloquea la acción
    And muestra un mensaje de permiso insuficiente

  Scenario: Administrador intenta cambiar prioridad en estado no permitido
    Given un ticket en estado "Closed"
    And el usuario tiene rol "Administrador"
    When intenta cambiar la prioridad
    Then el sistema bloquea la acción
    And informa que solo es posible en estados "Open" o "In-Progress"

  Scenario: Administrador intenta volver a Unassigned
    Given un ticket con prioridad "Medium"
    And el usuario tiene rol "Administrador"
    When intenta cambiar la prioridad a "Unassigned"
    Then el sistema bloquea la acción
    And informa que no es posible volver a "Unassigned"
```

**Notas:**
- Valor: Previene modificaciones no autorizadas y protege la integridad de la prioridad asignada
- Dependencias: Ticket Service (reglas de dominio), Frontend (validaciones de UI)

---

### HU-1.5: Visualizar justificación en el detalle del ticket

**Como** administrador  
**quiero** ver la justificación en el detalle del ticket cuando exista  
**para** entender el motivo del cambio de prioridad

#### Criterios de Aceptación (Gherkin)

```gherkin
@epic:gestion-prioridad @story:HU-1.5 @priority:media
Feature: Visualizar justificación en detalle
  Como administrador
  Quiero ver la justificación en el detalle del ticket cuando exista
  Para entender el motivo del cambio de prioridad

  Scenario: Detalle muestra justificación cuando existe
    Given un ticket con justificación de prioridad registrada
    When se renderiza el detalle del ticket
    Then se muestra la justificación registrada

  Scenario: Detalle sin justificación
    Given un ticket sin justificación de prioridad
    When se renderiza el detalle del ticket
    Then no se muestra la sección de justificación
```

**Notas:**
- Valor: Trazabilidad mínima del criterio de priorización, sin necesidad de historial completo
- Dependencias: Frontend (renderizado condicional en detalle), Ticket Service (campo en API response)

---

## 6. Resumen de Backlog por Prioridad

| Historia | Épica                         | Prioridad | Complejidad estimada                              |
| -------- | ----------------------------- | --------- | ------------------------------------------------- |
| HU-1.1   | Gestión de Prioridad (Admin)  | Alta      | Media (dominio + validaciones + API)              |
| HU-1.2   | Gestión de Prioridad (Admin)  | Alta      | Baja (lectura + componentes de visualización)     |
| HU-1.3   | Gestión de Prioridad (Admin)  | Media     | Baja (campo opcional + persistencia)              |
| HU-1.4   | Gestión de Prioridad (Admin)  | Alta      | Media (reglas de dominio + bloqueos en UI)        |
| HU-1.5   | Gestión de Prioridad (Admin)  | Media     | Baja (renderizado condicional en detalle)         |

### Orden de implementación sugerido

1. **HU-1.4** — Reglas de dominio primero: restricciones de rol, estado y reversión
2. **HU-1.1** — Lógica de asignación de prioridad sobre las reglas ya definidas
3. **HU-1.2** — Visualización en listado y detalle (frontend)
4. **HU-1.3** → **HU-1.5** — Justificación: captura en formulario y renderizado en detalle

  Scenario: Detalle sin justificacion
    Given un ticket sin justificacion de prioridad
    When se renderiza el detalle del ticket
    Then no se muestra la seccion de justificacion
```
