# IRIS — Guía de Instalación y Uso

## ¿Qué es IRIS?

**IRIS** (Intelligent Requirements & Insight Synthesizer) es un Custom Agent para VS Code que actúa como asistente de especificación funcional y descubrimiento de producto. Está diseñado para equipos que trabajan en MVPs o software en etapas tempranas y necesitan transformar ideas vagas, notas de reuniones o contexto de negocio en especificaciones funcionales estructuradas.

### ¿Qué hace IRIS?

| Entrada | Salida |
|---------|--------|
| Idea vaga (*"Quiero guardar los logs"*) | Épicas, historias de usuario, criterios de aceptación |
| Notas de reunión | Backlog estructurado con priorización |
| Contexto de negocio | Discovery completo con capacidades y journeys |
| Requerimientos existentes | Gapscan: detección de huecos y ambigüedades |
| Épica o historia de usuario | Escenarios de prueba en formato Gherkin (BDD) |
| Backlog existente | Checklist de pruebas (happy path, borde, negativos) |

### ¿Qué NO hace IRIS?

- ❌ No escribe código
- ❌ No diseña arquitectura técnica (eso es de ATLAS)
- ❌ No estima tiempos (eso es de CRONOS)
- ❌ No toma decisiones sin validación humana

---

## Ecosistema de Agentes

IRIS es parte de una trinidad de agentes especializados:

| Agente | Rol | Estado |
|--------|-----|--------|
| 👁 **IRIS** | Descubrimiento y análisis funcional | ✅ Disponible |
| 🏗 **ATLAS** | Arquitectura y diseño técnico | 🔜 Próximamente |
| ⏳ **CRONOS** | Estimación de tiempos y esfuerzo | 🔜 Próximamente |

---

## Prerrequisitos

Antes de instalar IRIS, asegúrate de tener:

### Obligatorios
- **VS Code** versión 1.99 o superior (soporte para Custom Agents)
- **GitHub Copilot** con suscripción activa (Individual, Business o Enterprise)
- **Extensión GitHub Copilot Chat** instalada y actualizada

### Recomendados
- **Modelo de lenguaje**: Se recomienda usar **Claude Opus 4.6** o **GPT 5.3 Codex** para mejores resultados en análisis de negocio. Puedes seleccionar el modelo desde el selector de modelos en el panel de Copilot Chat.
- **Extensiones adicionales**:
  - [Markdown All in One](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one) — Para mejor visualización de los artefactos generados
  - [Markdown Preview Enhanced](https://marketplace.visualstudio.com/items?itemName=shd101wyy.markdown-preview-enhanced) — Para previsualizar los documentos de especificación

---

## Instalación

### Método 1: Instalación Manual (Recomendado)

1. **Abre tu proyecto** en VS Code

2. **Verifica que exista** la carpeta `.github/agents/` en la raíz de tu proyecto. Si no existe, créala:
   ```
   mkdir -p .github/agents
   ```

3. **Copia el archivo** `iris.agent.md` a la carpeta `.github/agents/`:
   ```
   .github/
   └── agents/
       └── iris.agent.md    ← Archivo del agente
   ```

4. **Recarga VS Code** (Ctrl+Shift+P → "Developer: Reload Window")

5. **Verifica** que IRIS aparezca en el panel de Copilot Chat. Deberías poder mencionarlo con `@iris` en el chat.

### Método 2: Usando la Paleta de Comandos

1. Abre la paleta de comandos: `Ctrl+Shift+P` (Windows/Linux) o `Cmd+Shift+P` (Mac)
2. Ejecuta: **"Chat: New Custom Agent"**
3. Selecciona **"Workspace"** como ubicación
4. Nómbralo **"iris"**
5. VS Code generará un archivo `.agent.md` — reemplaza su contenido con el de `iris.agent.md` proporcionado

---

## Cómo Usar IRIS

### Invocación Básica

En el panel de Copilot Chat, usa `@iris` seguido de tu solicitud:

```
@iris Quiero crear un sistema de gestión de inventarios para una tienda pequeña
```

### Metodología CRAFT

IRIS utiliza el framework **CRAFT** para estructurar el análisis. Para mejores resultados, proporciona:

| Elemento | Qué incluir | Ejemplo |
|----------|-------------|---------|
| **C**ontexto | Situación actual, problema | "Tenemos una tienda con 500 productos y control manual en Excel" |
| **R**ol | Stakeholders, usuarios | "Dueño de tienda, empleados de mostrador, proveedor" |
| **A**cción | Objetivo principal | "Automatizar el control de stock y alertas de reposición" |
| **F**ormato | Tipo de salida | "Quiero un backlog completo con historias de usuario" |
| **T**arget | Audiencia del documento | "Para el equipo de desarrollo y el product owner" |

#### Ejemplo con CRAFT completo:

```
@iris

**Contexto**: Somos una startup de delivery de comida saludable. Actualmente
los pedidos se reciben por WhatsApp y se gestionan en una hoja de cálculo.
Tenemos 3 cocineros y 2 repartidores.

**Rol**: CEO de la startup, usuarios finales son los clientes que piden comida.

**Acción**: Necesitamos una app móvil para que los clientes puedan hacer
pedidos, personalizar sus platos y hacer seguimiento de la entrega.

**Formato**: Discovery completo con épicas y historias de usuario priorizadas.

**Target**: Equipo de desarrollo (3 devs) y un diseñador UX freelance.
```

### Tipos de Artefactos

Puedes solicitar artefactos específicos:

```
@iris Hazme un discovery de: [descripción del problema]
@iris Genera las épicas para: [contexto del proyecto]
@iris Escribe las historias de usuario para la épica: [nombre de la épica]
@iris Dame un backlog completo para: [proyecto]
@iris Mapea los journeys de usuario para: [flujo específico]
@iris Haz un gapscan de estos requerimientos: [requerimientos existentes]
@iris Tipo: scenarios [épica o historia de usuario]     → Escenarios Gherkin (BDD)
@iris Tipo: testchecklist [épica o historia de usuario]  → Checklist de pruebas
@iris Tipo: scenarios output: feature [épica]            → Salida en formato .feature
```

### Inferencia Dual ("Duelo de Mentes")

IRIS analiza problemas complejos desde dos perspectivas:

1. **Perspectiva Optimista**: Escenario ideal, alcance amplio
2. **Perspectiva Pragmática**: MVP mínimo, restricciones reales
3. **Síntesis**: Recomendación balanceada

Esto se activa automáticamente en:
- Definición de alcance de MVP
- Priorización de épicas
- Identificación de trade-offs

### Formato Gherkin (BDD)

IRIS usa formato **Gherkin estándar** para todos los criterios de aceptación y escenarios de prueba. Los keywords se mantienen en inglés (`Feature`, `Scenario`, `Given`, `When`, `Then`, `And`, `But`) y la narrativa se escribe en el idioma del usuario.

#### Ejemplo de salida Gherkin

```gherkin
@epic:gestion-pedidos @story:US-001 @priority:alta
Feature: Realizar pedido de comida saludable
       Como cliente de la app
       Quiero seleccionar platos y confirmar un pedido
       Para recibir comida saludable en mi domicilio

       Background:
              Given el cliente ha iniciado sesión en la app
              And existe al menos un plato disponible en el menú

       Scenario: Pedido exitoso con un plato
              Given el cliente está en la pantalla del menú
              When selecciona el plato "Ensalada César"
              And confirma el pedido
              And selecciona método de pago "Tarjeta de crédito"
              Then el sistema registra el pedido con estado "Confirmado"
              And el cliente recibe un número de seguimiento
              And el cocinero recibe la notificación del nuevo pedido

       Scenario: Pedido con personalización de plato
              Given el cliente está en la pantalla del menú
              When selecciona el plato "Bowl de Quinoa"
              And personaliza removiendo "aguacate"
              And agrega extra "pollo grillado"
              And confirma el pedido
              Then el sistema registra el pedido con las personalizaciones indicadas

       Scenario: Intento de pedido sin platos disponibles
              Given el cliente está en la pantalla del menú
              And no hay platos disponibles en este momento
              When intenta realizar un pedido
              Then el sistema muestra el mensaje "No hay platos disponibles en este momento"
              And sugiere horarios de disponibilidad

       Scenario Outline: Validación de monto mínimo de pedido
              Given el cliente tiene en el carrito platos por un total de <monto>
              When intenta confirmar el pedido
              Then el sistema <resultado>

              Examples:
                     | monto   | resultado                                          |
                     | $5.000  | muestra "El pedido mínimo es $10.000"              |
                     | $10.000 | permite confirmar el pedido                         |
                     | $25.000 | permite confirmar el pedido                         |
```

#### Tips para mejores resultados con Gherkin

- **Proporciona contexto rico**: Cuanto más detalle des sobre la épica o historia, más completos serán los escenarios
- **Especifica el tipo de escenarios**: Puedes pedir "solo happy path", "incluir casos de borde", o "enfocarse en seguridad"
- **Pide formato `.feature`**: Si necesitas output listo para copiar a archivos `.feature` de tu framework de pruebas
- **Usa tags de trazabilidad**: IRIS etiqueta automáticamente los escenarios con `@epic:`, `@story:`, `@priority:` para vincularlos al backlog

### Flujo de Trabajo Recomendado

```
1. 📥 Preparar contexto (notas, ideas, documentos)
       ↓
2. 🎯 Invocar IRIS con formato CRAFT
       ↓
3. 📋 Revisar estructura inicial generada
       ↓
4. ❓ Responder preguntas abiertas de IRIS
       ↓
5. 🔄 Iterar con feedback (refinar, ajustar)
       ↓
6. ✅ Validar con stakeholders / SME
       ↓
7. 📦 Exportar artefacto final
```

---

## Ejemplos Prácticos

### Ejemplo 1: Idea Vaga → Backlog Estructurado

**Input:**
```
@iris Quiero guardar los logs de mi aplicación
```

**IRIS responderá:**
1. Interpretará el contexto limitado
2. Hará preguntas CRAFT para completar información:
   - ¿Qué tipo de aplicación es?
   - ¿Qué tipo de logs? (errores, auditoría, métricas)
   - ¿Quién los consultará?
   - ¿Requisitos de retención?
3. Con las respuestas, generará el artefacto solicitado

### Ejemplo 2: Notas de Reunión → Épicas

**Input:**
```
@iris Tipo: epics

Notas de la reunión del 15/02:
- El cliente quiere que los usuarios puedan registrarse con Google
- Necesitan un dashboard con métricas de uso
- Quieren notificaciones push para promociones
- El admin debe poder gestionar usuarios y roles
- Integración con pasarela de pagos (Stripe o MercadoPago)
- Reportes exportables en PDF
```

### Ejemplo 3: Gapscan de Requerimientos Existentes

**Input:**
```
@iris Tipo: gapscan

Revisa estos requerimientos y encuentra huecos:

1. El usuario puede registrarse
2. El usuario puede hacer login
3. El usuario puede ver productos
4. El usuario puede agregar al carrito
5. El usuario puede pagar
```

**IRIS identificará gaps como:**
- ¿Recuperación de contraseña?
- ¿Búsqueda y filtros de productos?
- ¿Gestión de cantidades en carrito?
- ¿Métodos de pago soportados?
- ¿Confirmación de pedido?
- ¿Historial de compras?

### Ejemplo 4: Historia de Usuario → Escenarios Gherkin

**Input:**
```
@iris Tipo: scenarios

Historia de usuario:
Como administrador del sistema
quiero poder bloquear usuarios que violen las políticas de uso
para mantener la integridad de la plataforma

Contexto adicional:
- Existen 3 tipos de bloqueo: temporal (24h), extendido (7 días), permanente
- El admin recibe reportes de otros usuarios
- El usuario bloqueado debe ser notificado por email
- Se requiere registro de auditoría de todas las acciones de bloqueo
```

**IRIS generará** escenarios Gherkin cubriendo:
- Camino feliz: bloqueo exitoso de cada tipo
- Escenarios alternativos: bloqueo desde reporte, bloqueo preventivo
- Escenarios de error: intentar bloquear admin, usuario ya bloqueado
- Escenarios de auditoría: verificar registro de log
- `Scenario Outline` con `Examples` para los 3 tipos de bloqueo

### Ejemplo 5: Épica → Checklist de Pruebas

**Input:**
```
@iris Tipo: testchecklist

Épica: Gestión de Inventario
Historias incluidas:
1. Como dueño, quiero registrar productos nuevos
2. Como empleado, quiero actualizar el stock al recibir mercancía
3. Como dueño, quiero recibir alertas cuando el stock esté bajo
4. Como dueño, quiero ver reportes de movimientos de inventario
```

**IRIS generará** una checklist organizada por historia:
- ✅ Happy path por cada historia
- ⚠️ Casos de borde (stock = 0, producto duplicado, alerta múltiple)
- ❌ Casos negativos (campos vacíos, valores negativos, permisos insuficientes)
- 📊 Validaciones de datos (formatos, rangos, unicidad)

---

## Mejores Prácticas

### ✅ Haz esto

1. **Proporciona contexto rico** — Mientras más contexto des, mejores serán los requerimientos
2. **Usa el formato CRAFT** — Estructura tu entrada para obtener mejores salidas
3. **Valida con stakeholders** — IRIS marca supuestos como `[TBD]`; confírmalos con personas de negocio
4. **Itera** — No esperes perfección en la primera pasada; usa el loop de refinamiento
5. **Especifica el tipo de artefacto** — Di si quieres `discovery`, `epics`, `stories`, etc.
6. **Pide escenarios Gherkin para validación** — Genera escenarios de prueba para historias antes de pasarlas al equipo de desarrollo
7. **Usa el formato `.feature`** — Si tu equipo usa frameworks BDD (Cucumber, Behave, SpecFlow), pide la salida en formato `.feature`

### ❌ Evita esto

1. **No pidas código** — IRIS no escribe código; para eso usa Copilot directamente
2. **No pidas arquitectura** — Eso es dominio de ATLAS
3. **No asumas que el output es final** — Siempre valida con humanos
4. **No des contexto mínimo** — "Hazme un e-commerce" es demasiado vago sin CRAFT

---

## Solución de Problemas

| Problema | Solución |
|----------|----------|
| IRIS no aparece en el chat | Verifica que el archivo esté en `.github/agents/iris.agent.md` y recarga VS Code |
| Respuestas genéricas | Proporciona más contexto usando el formato CRAFT |
| IRIS escribe código | Recuérdale: *"No escribas código, solo requerimientos funcionales"* |
| Respuestas en inglés | Indica al inicio: *"Responde en español"* |
| El agente no se detecta | Verifica que tu versión de VS Code soporte Custom Agents (1.99+) |
| Modelo no disponible | Usa el selector de modelo en Copilot Chat para elegir uno disponible |

---

## Estructura de Archivos

```
tu-proyecto/
├── .github/
│   ├── agents/
│   │   └── iris.agent.md          ← Custom Agent de IRIS
└── IRIS_README.md                  ← Este archivo
```

---

## Referencia Rápida

```
@iris [tu idea o contexto]              → Discovery automático
@iris Tipo: discovery [contexto]        → Análisis del problema
@iris Tipo: epics [contexto]            → Generación de épicas
@iris Tipo: stories [épica]             → Historias de usuario
@iris Tipo: backlog [contexto]          → Backlog completo
@iris Tipo: journeys [flujo]            → Flujos de usuario
@iris Tipo: gapscan [requerimientos]    → Detección de huecos
@iris Tipo: scenarios [épica/historia]     → Escenarios Gherkin (BDD)
@iris Tipo: testchecklist [épica/historia]  → Checklist de pruebas
@iris Tipo: scenarios output: feature [épica] → Formato .feature exportable
```

---

## Créditos y Contexto

IRIS está inspirado en el agente de descubrimiento desarrollado por desarrolladores de Sofka, que utiliza:
- **CRAFT**: Framework de prompting estructurado (Contexto, Rol, Acción, Formato, Target)
- **Inferencia Dual**: Análisis desde múltiples perspectivas para resultados balanceados
- **Human-in-the-Loop**: Validación humana obligatoria en cada iteración

Adaptado como Custom Agent de VS Code para uso directo en el flujo de desarrollo del equipo.

---

## Licencia

Uso interno del equipo. Consultar con el equipo correspondiente para distribución externa.
