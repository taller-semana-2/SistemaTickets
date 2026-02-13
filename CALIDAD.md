# CALIDAD.md

## Anatomía de un Incidente

### 1. Contexto del Incidente

El incidente ocurrió durante el desarrollo de una arquitectura de microservicios que se comunicaba de forma asíncrona mediante eventos usando RabbitMQ, desplegado con Docker Compose.

Los microservicios involucrados fueron:
- assignment-service
- notification-service
- ticket-service

En este punto del desarrollo no existía el servicio de usuarios.

El objetivo era que, al crear un ticket, el evento correspondiente fuera consumido correctamente por **dos servicios distintos** (assignment-service y notification-service) sin duplicación ni pérdida de eventos.

---

### 2. Error (Acción Humana)

**Definición:** Acción humana incorrecta que originó el problema.

El error humano consistió en una **mala interpretación del funcionamiento de RabbitMQ y su modelo de mensajería**, específicamente en el uso de colas para distribuir eventos entre múltiples consumidores.

El equipo asumió incorrectamente que una misma cola permitiría que un mismo evento fuera consumido por más de un microservicio, sin comprender que RabbitMQ distribuye los mensajes de una cola entre los consumidores de forma competitiva (round-robin).

Este error se habría evitado mediante una lectura adecuada de la documentación oficial de RabbitMQ y una mejor comprensión de los tipos de exchange disponibles y su propósito.

---

### 3. Defecto (Bug en el Código / Configuración)

**Definición:** Imperfección técnica introducida en el sistema como consecuencia del error humano.

El defecto fue una **configuración incorrecta de RabbitMQ en el archivo `docker-compose`**, donde los microservicios consumidores estaban conectados a la misma cola sin utilizar un exchange adecuado para difusión de eventos.

Esto provocó que:
- Los eventos no fueran replicados.
- Cada mensaje fuera entregado solo a uno de los consumidores en lugar de a todos los servicios interesados.

La ausencia de un exchange de tipo `fanout` impidió que el evento fuera correctamente difundido a múltiples colas.

---

### 4. Fallo (Comportamiento Observable)

**Definición:** Manifestación del defecto durante la ejecución del sistema.

El fallo se manifestó cuando, al crear un ticket:
- En algunos casos solo se generaba la notificación.
- En otros casos solo se realizaba la asignación del ticket.
- Nunca se ejecutaban ambas acciones simultáneamente como se esperaba.

Desde la perspectiva del sistema, el comportamiento era inconsistente y no determinístico, ya que dependía de qué consumidor recibía el mensaje en ese momento.

Este fallo afectaba directamente la lógica de negocio y la confiabilidad del sistema.

---

### 5. Detección

El problema fue detectado al:
- Crear un ticket.
- Revisar la ejecución de los procesos de notificación y asignación.
- Observar que solo uno de los dos microservicios reaccionaba al evento generado.

El análisis de la ejecución evidenció que el evento no estaba siendo procesado por ambos consumidores.

---

### 6. Resolución

La solución consistió en:
- Implementar un **exchange de tipo `fanout`** en RabbitMQ.
- Crear colas independientes para cada microservicio consumidor.
- Enlazar dichas colas al exchange para que cada evento fuera enviado a todos los consumidores correspondientes.

Con esta configuración, cada evento generado por el ticket-service se difundía correctamente a assignment-service y notification-service sin duplicación ni pérdida.

---

### 7. Lecciones Aprendidas

- Comprender correctamente el modelo de mensajería es crítico en arquitecturas basadas en eventos.
- No todas las colas están diseñadas para difusión; el uso de exchanges es fundamental.
- La lectura de la documentación oficial de las herramientas evita errores de diseño tempranos.
- Los errores humanos en la etapa de configuración pueden generar fallos complejos en tiempo de ejecución.

## 2. Análisis de la Pirámide de Pruebas

### 2.1 Tesis: Por qué el proyecto requiere más pruebas Unitarias que E2E

El proyecto adopta una arquitectura basada en **Domain-Driven Design (DDD)** y **Event-Driven Architecture (EDA)**, compuesta por múltiples microservicios independientes (`ticket-service`, `assignment-service`, `notification-service`, `usuario-service`) que se comunican principalmente mediante eventos asíncronos a través de RabbitMQ.

En este contexto, la mayor parte de la complejidad del sistema **no reside en la interfaz de usuario ni en los flujos E2E**, sino en:
- La lógica de dominio encapsulada en cada servicio.
- El manejo correcto de eventos (publicación, consumo, idempotencia).
- La reacción adecuada de cada microservicio ante los cambios de estado del dominio.

Las pruebas E2E, aunque útiles, son:
- Costosas de ejecutar (requieren múltiples servicios, bases de datos y RabbitMQ).
- Frágiles ante cambios en infraestructura.
- Difíciles de diagnosticar cuando fallan.

Por el contrario, las pruebas unitarias:
- Son rápidas y determinísticas.
- Permiten validar reglas de negocio y handlers de eventos de forma aislada.
- Detectan errores humanos y defectos de diseño temprano, como el incidente ocurrido con la configuración incorrecta de RabbitMQ.

Por estas razones, el proyecto requiere una **base sólida de pruebas unitarias**, una capa intermedia enfocada en integración de eventos y contratos, y una cúspide reducida de pruebas E2E enfocadas únicamente en validar que el sistema completo está correctamente cableado.

---

### 2.2 Escenarios de Prueba de Alto Valor por Nivel

#### Nivel 1: Pruebas Unitarias (Base de la Pirámide)

**Escenario de Alto Valor:**  
Validación del handler de evento `TicketCreated` en `assignment-service`.

**Descripción:**  
Se prueba de forma aislada que, al recibir un evento `TicketCreated` válido:
- Se ejecuta la lógica de asignación correspondiente.
- Se persiste correctamente la asignación en la base de datos.
- Se respeta la idempotencia (el mismo evento no genera duplicados).

**Riesgo que mitiga:**  
- Errores en la lógica de dominio.
- Procesamiento incorrecto de eventos duplicados.
- Comportamiento inesperado ante cambios en el payload del evento.

**Justificación:**  
La lógica de negocio vive en los handlers y agregados de dominio. Si estos fallan, el sistema será incorrecto incluso si el flujo E2E funciona.

---

#### Nivel 2: Pruebas de Integración (Servicios + Infraestructura)

**Escenario de Alto Valor:**  
Publicación de un evento desde `ticket-service` y consumo correcto por `assignment-service` y `notification-service` mediante RabbitMQ.

**Descripción:**  
Se levanta un entorno controlado con RabbitMQ y se valida que:
- Un evento publicado en un exchange `fanout` es recibido por ambos consumidores.
- Cada servicio procesa el evento de forma independiente.
- No existe pérdida ni duplicación de mensajes.

**Riesgo que mitiga:**  
- Configuraciones incorrectas de exchanges, colas o bindings.
- Errores de integración entre servicios.
- Repetición del incidente de distribución incorrecta de eventos.

**Justificación:**  
Este nivel valida exactamente el tipo de defecto que ocurrió en el proyecto, sin el costo completo de una prueba E2E.

---

#### Nivel 3: Pruebas End-to-End (Cúspide de la Pirámide)

**Escenario de Alto Valor:**  
Flujo completo de creación y asignación de un ticket desde la perspectiva del usuario.

**Descripción:**  
Se valida que:
1. Un usuario crea un ticket.
2. El ticket genera eventos correctamente.
3. Un administrador ve la asignación.
4. El administrador recibe la notificación correspondiente.

**Riesgo que mitiga:**  
- Fallos de cableado entre servicios.
- Errores de configuración en despliegue.
- Problemas de comunicación entre frontend y backend.

**Justificación:**  
Las pruebas E2E no validan la lógica interna, sino que confirman que el sistema completo funciona como un todo. Por su alto costo, deben ser pocas y altamente estratégicas.

---

### 2.3 Conclusión

La Pirámide de Pruebas aplicada a este proyecto prioriza pruebas unitarias para proteger la lógica de dominio y el manejo de eventos, refuerza la capa de integración para validar la mensajería asíncrona, y limita las pruebas E2E a escenarios críticos de negocio.

Esta estrategia reduce costos, acelera el feedback y previene errores humanos y defectos estructurales como los ya experimentados durante el desarrollo.
