# HU-FE-01 — Refactor Estructural del Frontend: Home, Navbar y Consistencia de Layout

---

## 1. Título de HU

**Refactorizar la estructura visual y de navegación del frontend para establecer una base consistente, mantenible y con flujo de entrada correcto**

> Relacionada con: [Issue #72 — refactor(frontend): improve layout and navigation structure](https://github.com/taller-semana-2/SistemaTickets/issues/72)

---

## 2. Descripción

**Como** usuario que accede al sistema de tickets por primera vez,
**quiero** encontrar una página de inicio (Home) clara con acceso visible al Login,
**para** entender el sistema antes de autenticarme, y navegar con una experiencia visual coherente en todas las pantallas.

**Como** desarrollador frontend responsable del proyecto,
**quiero** una estructura de layout unificada, un Navbar alineado y componentes organizados de forma escalable,
**para** poder extender el frontend sin acumular deuda técnica adicional.

---

## 3. Objetivo de Negocio (Valor)

| Dimensión | Descripción |
|-----------|-------------|
| **Valor para el usuario** | El punto de entrada ya no es abruptamente el Login; el usuario puede orientarse antes de actuar |
| **Valor para el equipo** | Layout base consistente reduce el tiempo de incorporación de nuevos desarrolladores y facilita el mantenimiento |
| **Valor para el producto** | El frontend queda preparado para nuevas funcionalidades sin heredar deuda visual acumulada |
| **Riesgo que mitiga** | Evita que inconsistencias visuales crezcan al agregar nuevas pantallas sobre una base inestable |

---

## 4. Alcance / Fuera de Alcance

### ✅ En Alcance

- Implementar ruta y página `/home` (o `/`) como página de entrada al sistema
- Ruta raíz (`/`) debe renderizar `Home`, no redirigir a `/login` automáticamente
- Corregir alineación y equilibrio visual del Navbar (flexbox / grid consistente)
- Navbar debe mostrarse de forma consistente en todas las pantallas donde aplica
- Unificar estructura de layout: contenedores, márgenes y anchos en pantallas principales
- Revisar y ajustar el flujo de navegación inicial (Home → Login → pantallas protegidas)
- Mejorar organización interna de componentes y estilos (mantenibilidad básica)
- Ajustar o agregar tests unitarios/integración afectados por los cambios de routing y componentes

### ❌ Fuera de Alcance

- Cambios en lógica de negocio (creación de tickets, asignación, etc.)
- Modificación de endpoints del backend ni contratos de API
- Rediseño total o cambio de identidad visual (colores de marca, tipografías base)
- Introducción de nuevas bibliotecas de UI sin justificación explícita en PR
- Implementación de tests E2E (no obligatorio en esta iteración)
- Cambios en los servicios del backend (`ticket-service`, `assignment-service`, etc.)

---

## 5. Criterios de Aceptación en Gherkin

```gherkin
@epic:frontend-refactor @story:HU-FE-01 @priority:alta

Feature: Flujo de entrada y estructura del frontend
  Como usuario que accede al sistema de tickets
  Quiero una página de inicio clara y navegación consistente
  Para orientarme y acceder al sistema de forma natural

  Background:
    Given el servidor de desarrollo del frontend está corriendo
    And no existe ninguna sesión activa

  # ─── ESCENARIO 1: Home como punto de entrada ───────────────────────────────

  Scenario: La ruta raíz muestra la página Home
    Given el usuario navega a la ruta "/"
    When la aplicación termina de cargar
    Then se renderiza el componente "HomePage" (o equivalente)
    And el título visible de la página refleja que es la pantalla de bienvenida
    And no se produce redirección automática a "/login"

  # ─── ESCENARIO 2: Acción clara hacia Login desde Home ──────────────────────

  Scenario: Home contiene un elemento de acceso visible al Login
    Given el usuario está en la página Home ("/")
    When observa la pantalla principal
    Then existe al menos un elemento interactivo (botón o enlace) con texto legible que indica "Iniciar sesión" o equivalente
    And al hacer clic en ese elemento el usuario es dirigido a "/login"

  # ─── ESCENARIO 3: Login sigue siendo accesible directamente ────────────────

  Scenario: La ruta "/login" sigue funcionando de forma directa
    Given el usuario navega directamente a "/login"
    When la página carga
    Then se renderiza el componente de Login correctamente
    And el formulario de autenticación está presente y operable

  # ─── ESCENARIO 4: Navbar presente y con estructura consistente ─────────────

  Scenario Outline: El Navbar se renderiza en las pantallas que lo requieren
    Given el usuario autenticado navega a la ruta "<ruta>"
    When la pantalla carga
    Then el componente Navbar es visible en la pantalla
    And el Navbar ocupa el ancho completo del viewport sin desbordamiento horizontal
    And los elementos del Navbar están alineados horizontalmente sin solapamiento

    Examples:
      # Rutas protegidas confirmadas en AppRouter.tsx (no existe /dashboard ni /profile)
      | ruta           |
      | /tickets       |
      | /tickets/new   |
      | /notifications |

  # ─── ESCENARIO 5: Navbar ausente en pantallas que no lo requieren ──────────

  Scenario Outline: El Navbar no aparece en pantallas de autenticación
    Given el usuario navega a "<ruta_publica>"
    When la pantalla carga
    Then el componente Navbar NO está presente en el DOM

    Examples:
      | ruta_publica |
      | /            |
      | /login       |

  # ─── ESCENARIO 6: Layout consistente en pantallas principales ─────────────

  Scenario Outline: Las pantallas principales comparten la misma estructura de layout
    Given el usuario autenticado navega a "<ruta>"
    When la página termina de renderizar
    Then existe un contenedor raíz con clase de layout unificada
    And el contenido principal no desborda horizontalmente el viewport

    Examples:
      # Rutas protegidas confirmadas en AppRouter.tsx
      | ruta         |
      | /tickets     |
      | /tickets/new |

  # ─── ESCENARIO 7: Rutas existentes no se rompen ────────────────────────────

  Scenario Outline: Las rutas previamente funcionales siguen operativas tras el refactor
    Given el usuario navega a "<ruta_existente>"
    When la página carga
    Then el componente esperado se renderiza sin errores en consola
    And no aparece una pantalla de error 404 ni pantalla en blanco

    Examples:
      # Rutas confirmadas en AppRouter.tsx — /dashboard no existe en el proyecto
      | ruta_existente |
      | /login         |
      | /register      |
      | /tickets       |

  # ─── ESCENARIO 8: No se introducen dependencias no justificadas ────────────

  Scenario: El refactor no agrega paquetes npm sin justificación
    Given el archivo "package.json" antes y después del refactor
    When se compara la sección "dependencies" y "devDependencies"
    Then cualquier paquete nuevo agregado está documentado en el PR con justificación explícita
```

---

## 6. Notas Técnicas

> Estas notas orientan la implementación sin prescribir una reescritura total.

| Área | Observación |
|------|-------------|
| **Routing** | La redirección está en `src/routes/AppRouter.tsx`: `<Route path="/" element={<Navigate to="/login" replace />} />`. Cambiar este elemento por `<Route path="/" element={<HomePage />} />` es el único cambio de routing necesario. No hay `AuthGuard` separado. |
| **⚠️ Navbar — CRÍTICO** | El `Layout` en `AppRouter.tsx` muestra Navbar según `const isAuthPage = location.pathname === '/login' \|\| location.pathname === '/register'`. Si no se agrega `'/'` a esta condición, **el Navbar aparecerá en la página Home**. Corrección obligatoria: `location.pathname === '/login' \|\| location.pathname === '/register' \|\| location.pathname === '/'` |
| **⚠️ Navbar hace llamada API sin auth check** | `NavBar.tsx` llama a `notificationsApi.getNotifications()` directamente en `useEffect`. Si el Navbar llegara a renderizarse en una ruta pública (por error de condición), generará una llamada 401. Validar que la condición `isAuthPage` en `Layout` siempre excluya rutas públicas. |
| **Navbar — sistema de estilos** | Usa CSS plano con convención BEM (`.navbar`, `.navbar__brand`, `.navbar__links`, etc.) en `NavBar.css`. No usa Tailwind ni CSS Modules. Las correcciones de alineación deben hacerse dentro de este mismo archivo. |
| **Navbar — lógica de rol confirmada** | `const isAdmin = currentUser?.role === "ADMIN"` controla la visibilidad de los links de Notificaciones y Asignaciones. Esta lógica **debe preservarse intacta**. Solo corregir alineación de flex/grid. |
| **Layout wrapper** | No existe un `MainLayout` formal. El `Layout` interno de `AppRouter.tsx` es el único wrapper. Al agregar `'/'` a `isAuthPage`, las pantallas autenticadas ya tienen Navbar y las públicas no. Solo crear `MainLayout` separado si se quiere más claridad estructural. |
| **Estilos globales** | `src/styles/App.css` está **vacío**. `index.css` contiene estilos base. Sin conflicts de CSS global detectados. |
| **Tests** | Los tests existentes (`NotificationList.test.tsx`, `AssignmentList.test.tsx`, `index.test.tsx`) usan `<BrowserRouter>` directamente, **no renderizan `<App />` ni `<AppRouter />`**. No se romperán por el cambio de routing. Solo agregar tests nuevos para `HomePage`. |
| **No introducir** | React Router v6 ya presente. No hay Tailwind, UI kit, ni CSS Modules. Mantener CSS plano BEM como sistema existente. |

---

## 7. Definition of Done (DoD)

- [ ] La ruta `/` renderiza `HomePage` sin redirección automática a `/login`
- [ ] `HomePage` contiene un elemento interactivo que dirige a `/login`
- [ ] El Navbar está alineado y sin desbordamiento en todas las rutas protegidas
- [ ] El Navbar **no** aparece en las rutas públicas (`/` y `/login`)
- [ ] Existe una estructura de layout unificada para las pantallas autenticadas (ej. `MainLayout`)
- [ ] Todas las rutas previamente funcionales siguen operativas (verificado por tests y revisión manual)
- [ ] Los tests unitarios/integración existentes pasan sin errores
- [ ] Se agregan o actualizan tests que cubren los escenarios 1, 2, 3 y 4 (como mínimo)
- [ ] No se introducen dependencias npm nuevas sin justificación documentada en el PR
- [ ] El PR describe explícitamente qué archivos se modificaron y por qué
- [ ] Revisión de código aprobada por al menos 1 revisor
- [ ] No hay errores ni warnings críticos en consola del navegador en las rutas principales

---

## 8. Riesgos y Supuestos

### Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|-------------|---------|------------|
| R1 | El cambio de routing rompe guards de autenticación existentes | **Baja** ✅ | Alto | **VALIDADO — bajo riesgo real.** La redirección `/` → `/login` es un `<Navigate>` directo en `AppRouter.tsx`, no un guard component. `ProtectedRoute` solo protege rutas específicas y no se ve afectado por agregar una ruta `/` nueva. |
| R2 | Estilos CSS globales sin scope afectan otras pantallas al modificarlos | **Baja** ✅ | Medio | **VALIDADO — bajo riesgo real.** `App.css` está vacío. `NavBar.css` usa clases BEM bien nombradas (`.navbar__*`) sin conflictos detectados. `index.css` contiene estilos base genéricos. |
| R3 | Tests existentes que renderizan `<App />` fallan por el nuevo routing | **Muy Baja** ✅ | Bajo | **REFUTADO — no aplica.** Ningún test existente renderiza `<App />` ni `<AppRouter />`. Todos usan `<BrowserRouter>` con componentes individuales. El riesgo real es casi nulo. |
| R4 | **⚠️ El Navbar aparece en Home si no se actualiza la condición `isAuthPage`** | **Alta** 🔴 | **Alto** | **CONFIRMADO — riesgo REAL y concreto.** En `AppRouter.tsx`, el `Layout` excluye Navbar solo si `pathname === '/login' \|\| pathname === '/register'`. Al agregar la ruta `/` → `HomePage`, el Navbar **se mostrará en Home automáticamente**. La corrección es obligatoria: agregar `\|\| pathname === '/'` a la condición. |
| R5 | El refactor se extiende más allá del alcance definido | Media | Alto | Control de proceso. Aplicar la regla de **refactor incremental**: un PR por área (routing/Home, corrección Navbar, layout unificado). No mezclar cambios. |

### Supuestos

| ID | Supuesto |
|----|----------|
| S1 | El sistema de routing ya usa React Router (v5 o v6); no se cambiará de librería |
| S2 | Existe al menos una pantalla protegida por autenticación (`/dashboard` o similar) donde el Navbar debe mostrarse |
| S3 | El sistema de estilos actual (CSS, SCSS o Tailwind) se mantiene; no se migrará de sistema en esta HU |
| S4 | Los tests unitarios/integración usan Vitest + React Testing Library ✅ **CONFIRMADO** — verificado en `vite.config.ts` y todos los archivos de test |
| S5 | ~~`[TBD]`~~ → **RESUELTO** ✅ — No existe `AuthGuard` component separado. La redirección es `<Route path="/" element={<Navigate to="/login" replace />} />` directamente en `AppRouter.tsx` línea ~35. |
| S6 | ~~`[TBD]`~~ → **RESUELTO** ✅ — No existe ruta `/dashboard`. Las rutas post-login son `/tickets` (todos los usuarios), `/notifications` y `/assignments` (solo ADMIN). El Navbar usa `/tickets` como destino del logo. Los Scenario Outline de la HU han sido corregidos en consecuencia. |

---

## Preguntas Abiertas — Estado post-análisis de código

| # | Pregunta | Estado | Respuesta |
|---|----------|--------|----------|
| 1 | ¿Existe `AuthGuard` o `PrivateRoute` que redirige `/` → `/login`? | ✅ **Respondida** | No hay componente guard para `/`. La redirección es `<Route path="/" element={<Navigate to="/login" replace />} />` en `AppRouter.tsx`. Cambio directo y localizado. |
| 2 | ¿Qué pantallas protegidas existen actualmente? | ✅ **Respondida** | `/tickets`, `/tickets/new`, `/tickets/:id` (todos los auth); `/notifications`, `/assignments` (solo ADMIN). **No existe `/dashboard` ni `/profile`** — los ejemplos de la HU fueron corregidos. |
| 3 | ¿El Navbar tiene lógica condicional por rol? | ✅ **Respondida** | Sí. `const isAdmin = currentUser?.role === 'ADMIN'` controla la visibilidad de los links de Notificaciones y Asignaciones. **Esta lógica debe preservarse sin cambios.** |
| 4 | ¿Existen tests E2E activos que puedan verse afectados? | ✅ **Respondida** | **No.** La carpeta `e2e/tests/` está vacía. Sin riesgo de regresión en E2E. |
| 5 | ¿Hay sistema de diseño o guía de estilo para la `HomePage`? | ✅ **Respondida** | No hay design system formal. El sistema es CSS plano con BEM. La `HomePage` debe seguir la misma paleta del Navbar (gradiente `#667eea → #764ba2`) para consistencia visual mínima. |

---

## Checklist de Validación

- [x] El output parte del problema de negocio (experiencia de usuario inconsistente y deuda técnica de layout)
- [x] La historia tiene valor explícito (usuario final + equipo de desarrollo)
- [x] Los supuestos están marcados con `[TBD]` donde corresponde
- [x] Existe lista consolidada de preguntas abiertas
- [x] Los criterios de aceptación usan sintaxis Gherkin válida
- [x] Existe al menos un escenario de camino feliz por cada área (routing, Navbar, layout)
- [x] Variaciones relevantes modeladas con `Scenario Outline` + `Examples`
- [x] Escenarios trazables a épica/historia por tags (`@epic:frontend-refactor @story:HU-FE-01`)
- [x] Se cubren escenarios de error/borde (rutas que no deben mostrar Navbar, rutas que no deben romperse)

---

> **Nota de priorización:** Esta HU debe completarse antes de implementar cualquier nueva pantalla o funcionalidad de frontend, ya que establece la estructura base sobre la que se construirá.
> Refactor incremental recomendado: **PR 1** — routing/Home → **PR 2** — Navbar → **PR 3** — layout unificado.
