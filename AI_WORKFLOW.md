# AI_WORKFLOW.md

## 1. Propósito del documento

Este documento define la **estrategia de interacción con Inteligencia Artificial (IA)** adoptada por el equipo para el desarrollo del *Sistema de Tickets / Soporte*.

El objetivo es utilizar la IA no solo como asistente técnico, sino también como una **Puerta de Calidad (Quality Gate)** previa a cada commit, permitiendo detectar riesgos técnicos, deuda inadvertida y violaciones a principios de calidad antes de que el código ingrese al repositorio.

---

## 2. Principios rectores (AI-First con Control Humano)

1. **La IA no decide arquitectura**  
   Las decisiones estructurales, de dominio y de integración son responsabilidad exclusiva del equipo humano.

2. **La IA asiste, no reemplaza**  
   La IA propone, analiza y señala riesgos; el equipo decide.

3. **Calidad antes del commit**  
   Ningún cambio se integra sin pasar por una validación explícita de calidad apoyada por IA.

4. **La IA como Quality Gate, no como aprobador**  
   La IA identifica problemas; la aprobación final siempre es humana.

5. **Aprendizaje consciente**  
   Cada uso de IA debe contribuir al entendimiento del sistema, no ocultarlo.

---

## 3. Roles y responsabilidades frente a la IA

### 👨‍💻 Developers (Backend / Frontend)

* Usan la IA para:
  * Generar boilerplate y prototipos
  * Refactorizar código
  * Proponer pruebas unitarias o de integración
* Son responsables de:
  * Ejecutar la revisión de calidad asistida por IA antes del commit
  * Ajustar el código según los hallazgos
  * No delegar decisiones de diseño a la IA

---

### 🧑‍🔬 QA Engineer

* Define los **criterios de calidad** que la IA debe evaluar:
  * Testabilidad
  * Desacoplamiento
  * Cumplimiento de principios SOLID
  * Manejo correcto de eventos (EDA)
* Valida:
  * Que la IA esté siendo usada como gate de calidad
  * Que los riesgos identificados hayan sido tratados
* Supervisa que la IA no introduzca:
  * Acoplamiento innecesario
  * Lógica duplicada
  * Dependencias ocultas

---

## 4. Metodología de interacción con IA

### 4.1 Flujo estándar de desarrollo

1. Definición humana del cambio
2. Implementación inicial (con o sin IA)
3. Revisión manual del desarrollador
4. **Quality Gate asistido por IA**
5. Corrección de hallazgos
6. Validación QA
7. Commit al repositorio

---

## 5. IA como Puerta de Calidad (Quality Gate)

Antes de **cada commit**, el desarrollador debe ejecutar una revisión con IA solicitando explícitamente un análisis de calidad.

### 5.1 Objetivo del Quality Gate

La IA debe actuar como un **revisor técnico crítico**, enfocado en detectar:

* Errores de diseño
* Deuda técnica inadvertida
* Violaciones a principios SOLID
* Riesgos en flujos EDA
* Problemas de testabilidad
* Uso incorrecto de infraestructura (RabbitMQ, Docker, DB)

---

### 5.2 Checklist de Calidad Evaluado por la IA

La IA debe evaluar explícitamente:

- ¿Existe acoplamiento innecesario?
- ¿La lógica de dominio está claramente separada?
- ¿El código es testeable?
- ¿Los handlers de eventos son idempotentes?
- ¿Se introducen configuraciones frágiles?
- ¿Se incrementa la deuda técnica?

---

### 5.3 Estructura obligatoria del prompt de Quality Gate

Antes del commit, el desarrollador debe usar un prompt con la siguiente estructura:

- Contexto del proyecto (DDD + EDA)
- Rol de la IA: *Quality Gate / Revisor Técnico*
- Descripción del cambio realizado
- Código modificado
- Pregunta explícita:
  > “¿Qué riesgos técnicos, de diseño o de calidad introduce este cambio?”

---

## 6. Tipos de interacciones permitidas

### ✅ Permitidas

* Análisis de calidad
* Revisión de diseño
* Detección de deuda técnica
* Sugerencias de mejora
* Evaluación de testabilidad
* Análisis de flujos de eventos

---

### ❌ No permitidas

* Aprobar código automáticamente
* Introducir arquitectura nueva sin consenso
* Manejo de secretos o credenciales
* Reemplazar revisiones humanas

---

## 7. Documentos clave usados como contexto

Para que la IA funcione correctamente como Quality Gate, se debe proveer:

* Arquitectura del sistema
* Principios DDD y EDA adoptados
* AI_WORKFLOW.md
* DEUDA_TECNICA.md
* CALIDAD.md

---

## 8. Validación y control de calidad (QA)

El QA valida que:

* El Quality Gate con IA se ejecutó antes del commit
* Los hallazgos críticos fueron atendidos
* No se introdujo deuda técnica innecesaria
* Las pruebas existentes siguen siendo válidas

---

## 9. Riesgos identificados y mitigación

| Riesgo                               | Mitigación                                 |
|------------------------------------|--------------------------------------------|
| Confianza excesiva en la IA         | Aprobación humana obligatoria               |
| Introducción de deuda inadvertida   | IA como Quality Gate + QA                   |
| Acoplamiento en microservicios     | Revisión EDA y DDD asistida por IA           |
| Falta de pruebas                    | Validación explícita de testabilidad        |

---

## 10. Evolución del documento

Este documento es **vivo** y evolucionará conforme el equipo:
- Mejore su madurez técnica
- Ajuste sus criterios de calidad
- Profundice en el uso responsable de IA
