# AI_WORKFLOW.md

## 1. Propósito del documento

Este documento define la **estrategia de interacción con Inteligencia Artificial (IA)** adoptada por el equipo para el desarrollo del *Sistema de Tickets / Soporte*.

El objetivo es usar la IA como un **asistente técnico (Junior Developer)**, manteniendo siempre el control humano sobre las decisiones de arquitectura, calidad y seguridad.

---

## 2. Principios rectores (AI-First)

1. **La IA no decide arquitectura**: las decisiones estructurales son humanas.
2. **La IA genera, el equipo valida**: ningún código pasa a producción sin revisión.
3. **Calidad sobre velocidad**: la IA acelera, pero no justifica deuda técnica.
4. **QA como guardián**: el rol QA valida código, pruebas y riesgos del output generado por IA.

---

## 3. Roles y responsabilidades frente a la IA

### 👨‍💻 Developers (Backend / Frontend)

* Usar IA para:

  * Generar estructuras base (boilerplate)
  * Prototipos de endpoints
  * Componentes de UI
* Refinar y adaptar el código generado.
* Documentar prompts relevantes.

### 🧑‍🔬 QA Engineer

* Revisar código generado por IA bajo criterios de:

  * Calidad
  * Seguridad
  * Testabilidad
  * Desacoplamiento
* Definir y ejecutar pruebas automáticas.
* Validar que la IA no introduzca malas prácticas.

---

## 4. Metodología de interacción con IA

### 4.1 Flujo estándar

1. Definición humana del problema
2. Prompt claro y contextualizado a la IA
3. Generación de código / propuesta
4. Revisión técnica humana
5. Ajustes manuales
6. Validación QA
7. Commit al repositorio

---

## 5. Tipos de interacciones permitidas

### ✅ Permitidas

* Generación de código base
* Refactorización
* Sugerencias de tests
* Explicaciones técnicas

### ❌ No permitidas

* Copiar código sin revisión
* Decisiones de arquitectura sin consenso
* Manejo de secretos o credenciales

---

## 6. Documentos clave usados como contexto

Antes de interactuar con la IA, se debe proporcionar:

* Descripción del proyecto
* Arquitectura definida
* Rol (Developer / QA)
* Stack tecnológico

---

## 7. Estrategia de prompting

### 7.1 Estructura recomendada de prompt

* Contexto del proyecto
* Rol de la IA
* Tarea específica
* Restricciones técnicas
* Criterios de calidad

---

## 8. Validación y control de calidad (QA)

El QA valida que:

* El código generado es testeable
* Existen pruebas automáticas
* No hay dependencias innecesarias
* El flujo asíncrono se mantiene desacoplado

---

## 9. Riesgos identificados y mitigación

| Riesgo                     | Mitigación              |
| -------------------------- | ----------------------- |
| Código inseguro            | Revisión manual + tests |
| Acoplamiento               | Revisión arquitectónica |
| Dependencia excesiva de IA | Decisiones humanas      |

---

## 10. Evolución del documento

Este documento es **vivo** y se actualizará conforme evolucione el proyecto y el uso de IA.
