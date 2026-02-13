# DEUDA_TECNICA.md

## Registro de Deuda Técnica

Este documento registra las deudas técnicas asumidas durante el desarrollo del proyecto, identificadas desde la perspectiva del **Product Owner**, considerando las restricciones de tiempo, el objetivo de entrega de un MVP y el contexto académico del equipo.

Las deudas se clasifican según el **Cuadrante de Martin Fowler**, distinguiendo entre decisiones prudentes o imprudentes, y deliberadas o inadvertidas.

---

## 1. Deuda Prudente / Deliberada

### 1.1 Configuración mínima de RabbitMQ
**Descripción:**  
Se utilizó una configuración básica de RabbitMQ, suficiente para el funcionamiento del MVP, sin profundizar inicialmente en patrones avanzados de mensajería.

**Motivo:**  
Prioridad en la entrega rápida del MVP y aprendizaje progresivo de EDA.

**Impacto:**  
Riesgo de errores de diseño en la distribución de eventos (materializado posteriormente).

**Plan de pago:**  
Refinar configuraciones, documentar exchanges y estandarizar contratos de eventos.

---

### 1.2 Cobertura limitada de pruebas E2E
**Descripción:**  
El sistema cuenta únicamente con una prueba End-to-End.

**Motivo:**  
Las pruebas E2E tienen alto costo de implementación y mantenimiento, especialmente en una arquitectura de microservicios con mensajería asíncrona.

**Impacto:**  
Posibles fallos de integración no detectados automáticamente.

**Plan de pago:**  
Agregar pruebas E2E solo para flujos críticos adicionales.

---

### 1.3 Uso de un algoritmo simple para asignaciones
**Descripción:**  
La asignación de tickets a administradores se realizó mediante un randomizador de prioridad.

**Motivo:**  
Necesidad de demostrar el flujo completo de negocio en el MVP sin definir reglas complejas.

**Impacto:**  
La lógica no refleja un escenario realista ni óptimo.

**Plan de pago:**  
Reemplazar por reglas de negocio basadas en carga, roles o SLA.

---

## 2. Deuda Prudente / Inadvertida

### 2.1 Uso inicial de estructuras de Django sin aplicar SOLID
**Descripción:**  
Se partió de un diseño basado en views y estructuras por defecto de Django, lo que generó acoplamiento y dificultades para mantener principios SOLID.

**Motivo:**  
Facilidad inicial y curva de aprendizaje reducida.

**Impacto:**  
Necesidad posterior de refactorización para desacoplar lógica de negocio.

**Estado:**  
Corregido durante el desarrollo.

---

### 2.2 Documentación limitada
**Descripción:**  
La documentación del sistema se limita a un archivo README general, sin detallar arquitectura, eventos ni decisiones técnicas.

**Motivo:**  
Enfoque en funcionalidad y entrega del MVP.

**Impacto:**  
Mayor dificultad para onboarding y mantenimiento futuro.

**Plan de pago:**  
Ampliar documentación técnica y decisiones de arquitectura.

---

## 3. Deuda Imprudente / Inadvertida

### 3.1 Desconocimiento inicial del modelo de mensajería de RabbitMQ
**Descripción:**  
Se asumió incorrectamente que una cola podía distribuir eventos a múltiples consumidores, sin utilizar exchanges adecuados.

**Motivo:**  
RabbitMQ y EDA eran tecnologías nuevas para el equipo.

**Impacto:**  
Comportamiento incorrecto del sistema (eventos no procesados por todos los servicios).

**Estado:**  
Corregido mediante el uso de exchanges tipo fanout.

---

### 3.2 Falta de automatización de pruebas
**Descripción:**  
Aunque existen pruebas en todas las áreas, estas no están integradas en un pipeline automatizado.

**Motivo:**  
Limitaciones de tiempo y foco en desarrollo funcional.

**Impacto:**  
Mayor riesgo de regresiones y dependencia de ejecución manual.

**Plan de pago:**  
Integrar pruebas en CI/CD.

---

## 4. Deuda Imprudente / Deliberada

### 4.1 Ausencia de observabilidad (logs, métricas, alertas)
**Descripción:**  
El sistema carece de una estrategia clara de logging y monitoreo.

**Motivo:**  
Se consideró fuera del alcance del MVP.

**Impacto:**  
Dificultad para detectar y diagnosticar fallos en tiempo de ejecución.

**Plan de pago:**  
Incorporar logging estructurado y métricas básicas.

---

### 4.2 Uso exclusivo de Docker Compose para todos los entornos
**Descripción:**  
Docker Compose se utiliza tanto para desarrollo como para simular entornos completos.

**Motivo:**  
Simplicidad y velocidad en el desarrollo.

**Impacto:**  
Falta de separación clara de entornos y riesgos al escalar.

**Plan de pago:**  
Definir estrategias diferenciadas para desarrollo y despliegue productivo.

---

## Conclusión

La deuda técnica acumulada es consistente con un proyecto orientado a la entrega rápida de un MVP y al aprendizaje académico.  
Gran parte de la deuda fue asumida de forma consciente y prudente, y los principales riesgos estructurales ya han sido identificados y, en algunos casos, mitigados.

El registro de esta deuda permite planificar su pago futuro y demuestra una gestión responsable desde el rol de Product Owner.
