## Contexto Interpretado
El sistema asigna prioridad de forma automatica y aleatoria. Se requiere que el administrador defina manualmente la prioridad en el panel, con valores Unassigned (por defecto), Low, Medium y High. Solo roles administradores pueden reasignar prioridad y solo cuando el ticket este en Open o In-Progress. No habra auditoria, trazabilidad ni historial. No se envian notificaciones. La justificacion es opcional, pero si se ingresa debe mostrarse en el detalle del ticket. No se permite volver a Unassigned despues de haber asignado una prioridad.

## Objetivos Identificados
- Permitir a administradores asignar prioridad manualmente
- Eliminar asignacion aleatoria de prioridad
- Restringir cambios por rol y estado del ticket
- Mostrar justificacion si se ingreso

## Capacidades Necesarias
- Mostrar prioridad actual (incluyendo Unassigned por defecto)
- Permitir cambiar prioridad a Low/Medium/High
- Bloquear asignacion a Unassigned despues de haber definido otra prioridad
- Validar rol administrador
- Validar estados Open o In-Progress
- Capturar justificacion opcional y mostrarla en detalle

## Epicas
1) Gestion de prioridad por administradores

## Historias de Usuario (tecnicas con Gherkin)

**Como** administrador
**quiero** cambiar la prioridad de un ticket en estado Open o In-Progress
**para** reflejar su urgencia real

### Criterios de Aceptacion (Gherkin):
```gherkin
Feature: Cambiar prioridad de ticket por administrador

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

---

**Como** administrador
**quiero** ver la prioridad actual en el listado y detalle del ticket
**para** decidir cambios sin pasos adicionales

### Criterios de Aceptacion (Gherkin):
```gherkin
Feature: Visualizar prioridad del ticket

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

---

**Como** administrador
**quiero** que la justificacion sea opcional al cambiar prioridad
**para** no bloquear cambios urgentes

### Criterios de Aceptacion (Gherkin):
```gherkin
Feature: Justificacion opcional en cambio de prioridad

  Scenario: Cambio con justificacion
    Given un ticket en estado "Open"
    And el usuario tiene rol "Administrador"
    When selecciona la prioridad "High" e ingresa una justificacion
    And confirma el cambio
    Then la prioridad se actualiza
    And la justificacion se guarda

  Scenario: Cambio sin justificacion
    Given un ticket en estado "In-Progress"
    And el usuario tiene rol "Administrador"
    When selecciona la prioridad "Low" sin ingresar justificacion
    And confirma el cambio
    Then la prioridad se actualiza
```

---

**Como** administrador
**quiero** que el sistema bloquee cambios de prioridad si el usuario no es administrador, el estado no es valido o se intenta volver a Unassigned
**para** asegurar el control de permisos y proceso

### Criterios de Aceptacion (Gherkin):
```gherkin
Feature: Restricciones por rol, estado y prioridad

  Scenario: Usuario sin rol administrador intenta cambiar prioridad
    Given un ticket en estado "Open"
    And el usuario tiene rol "Agente"
    When intenta cambiar la prioridad
    Then el sistema bloquea la accion
    And muestra un mensaje de permiso insuficiente

  Scenario: Administrador intenta cambiar prioridad en estado no permitido
    Given un ticket en estado "Closed"
    And el usuario tiene rol "Administrador"
    When intenta cambiar la prioridad
    Then el sistema bloquea la accion
    And informa que solo es posible en estados "Open" o "In-Progress"

  Scenario: Administrador intenta volver a Unassigned
    Given un ticket con prioridad "Medium"
    And el usuario tiene rol "Administrador"
    When intenta cambiar la prioridad a "Unassigned"
    Then el sistema bloquea la accion
    And informa que no es posible volver a "Unassigned"
```

---

**Como** administrador
**quiero** ver la justificacion en el detalle del ticket cuando exista
**para** entender el motivo del cambio

### Criterios de Aceptacion (Gherkin):
```gherkin
Feature: Visualizar justificacion en detalle

  Scenario: Detalle muestra justificacion cuando existe
    Given un ticket con justificacion de prioridad
    When se renderiza el detalle del ticket
    Then se muestra la justificacion registrada

  Scenario: Detalle sin justificacion
    Given un ticket sin justificacion de prioridad
    When se renderiza el detalle del ticket
    Then no se muestra la seccion de justificacion
```