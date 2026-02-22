# Instrucciones de Resolución de Conflictos — PR #109

> **Branch:** `fix/bug-httponly-cookies` → `develop`
> **Naturaleza:** Bugfix de seguridad (migración localStorage → HttpOnly cookies)
> **Principio rector:** Los cambios del bugfix **siempre prevalecen**. Las mejoras de `develop` se re-inyectan solo si son aditivas y no contradicen la nueva arquitectura de autenticación.

---

## Resumen de Conflictos

| # | Archivo | Estrategia |
|---|---------|------------|
| 1 | `backend/assignment-service/assessment_service/settings.py` | Ours + hardening |
| 2 | `backend/notification-service/notification_service/settings.py` | Ours + hardening |
| 3 | `backend/ticket-service/ticket_service/settings.py` | Ours + hardening |
| 4 | `backend/users-service/user_service/settings.py` | Ours + hardening |
| 5 | `frontend/src/components/ProtectedRoute.tsx` | Ours 100% |
| 6 | `frontend/src/pages/assignments/AssignmentList.tsx` | Ours 100% |
| 7 | `frontend/src/pages/navbar/NavBar.tsx` | Ours 100% |
| 8 | `frontend/src/pages/tickets/TicketList.tsx` | Ours 100% |
| 9 | `frontend/src/services/ticketApi.ts` | Ours 100% |

---

## Fase 1 — Frontend (Take Ours, sin edición adicional)

### Razón

`develop` usa `authService` + `localStorage` para autenticación. El bugfix reemplaza todo esto con `useAuth()` context + HttpOnly cookies. Las dos versiones son **mutuamente excluyentes** — no hay integración parcial posible.

### Archivos y qué preservar

#### 1. `frontend/src/components/ProtectedRoute.tsx`

**Tomar:** Versión del bugfix íntegra.

Debe importar desde `../context/AuthContext` y usar `useAuth()`.
NO debe importar `authService`, `getAccessToken`, ni tener función `isTokenExpired`.
Debe tener un estado `loading` que muestre "Cargando..." mientras verifica sesión.

#### 2. `frontend/src/pages/assignments/AssignmentList.tsx`

**Tomar:** Versión del bugfix íntegra.

Debe usar `useEffect` directo (NO `useFetch` hook).
Debe tener lógica de `handleComplete` que transiciona OPEN → IN_PROGRESS → CLOSED.
Las funciones API (`getAssignments`, `getTickets`) NO llevan parámetro `signal`.

#### 3. `frontend/src/pages/navbar/NavBar.tsx`

**Tomar:** Versión del bugfix íntegra.

Debe importar `useAuth` desde `../../context/AuthContext`.
NO debe importar `authService` ni `useFetch`.
`handleLogout` debe ser `async` y llamar `await logout()` del contexto.
`loadUnreadCount` debe usar `useCallback`.

#### 4. `frontend/src/pages/tickets/TicketList.tsx`

**Tomar:** Versión del bugfix íntegra.

Debe usar `useAuth()` para obtener `user`.
NO debe importar `authService`.
Filtro de tickets por usuario: `String(ticket.user_id) === String(user.id)` (cast explícito).

#### 5. `frontend/src/services/ticketApi.ts`

**Tomar:** Versión del bugfix íntegra.

`createResponse` debe recibir `adminId` como **tercer parámetro explícito**.
NO debe leer de `localStorage`.
Ningún método lleva parámetro `signal: AbortSignal`.

---

## Fase 2 — Backend Settings (Take Ours + Ediciones de Hardening)

### Razón

`develop` agregó mejoras de producción legítimas que el bugfix no incluye:
- `DEBUG` default `"false"` (seguridad)
- `ALLOWED_HOSTS` dinámico desde variable de entorno
- Desactivación de Browsable API en producción
- Bloque de security hardening (XSS filter, X-Frame-Options, cookie secure)

Estas mejoras son **aditivas** y no interfieren con la cookie auth.

### Procedimiento para cada archivo

Después de hacer `git checkout --ours` en los 4 settings.py, aplicar las siguientes ediciones:

---

#### 2.1 — `backend/assignment-service/assessment_service/settings.py`

**Edición A — DEBUG default:**
```python
# CAMBIAR:
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
# POR:
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
```

**Edición B — ALLOWED_HOSTS dinámico:**
```python
# CAMBIAR:
ALLOWED_HOSTS = []
# POR:
_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]
```

**Edición C — Disable Browsable API.** Agregar inmediatamente DESPUÉS del bloque `REST_FRAMEWORK = { ... }`:
```python
# Disable Browsable API in production (security: prevents endpoint/model exposure)
if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
    )
```

**Edición D — Security hardening.** Agregar AL FINAL del archivo (después de `CSRF_TRUSTED_ORIGINS`):
```python
# =============================================================================
# Security hardening (production)
# =============================================================================
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
```

---

#### 2.2 — `backend/notification-service/notification_service/settings.py`

**Edición A — DEBUG default:**
```python
# CAMBIAR:
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
# POR:
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
```

**Edición B — ALLOWED_HOSTS:** Ya es dinámico en ambas ramas. No necesita cambio.

**Edición C — Disable Browsable API.** Agregar inmediatamente DESPUÉS del bloque `REST_FRAMEWORK = { ... }`:
```python
# Disable Browsable API in production (security: prevents endpoint/model exposure)
if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
    )
```

**Edición D — Security hardening.** Agregar AL FINAL del archivo:
```python
# =============================================================================
# Security hardening (production)
# =============================================================================
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
```

---

#### 2.3 — `backend/ticket-service/ticket_service/settings.py`

**Edición A — DEBUG default:**
```python
# CAMBIAR:
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
# POR:
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
```

**Edición B — ALLOWED_HOSTS:** Ya es dinámico en ambas ramas. No necesita cambio.

**Edición C — Disable Browsable API.** Agregar inmediatamente DESPUÉS del bloque `REST_FRAMEWORK = { ... }`:
```python
# Disable Browsable API in production (security: prevents endpoint/model exposure)
if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
    )
```

**Edición D — Security hardening.** Agregar AL FINAL del archivo:
```python
# =============================================================================
# Security hardening (production)
# =============================================================================
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
```

---

#### 2.4 — `backend/users-service/user_service/settings.py`

**Edición A — DEBUG default:**
```python
# CAMBIAR:
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
# POR:
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
```

**Edición B — ALLOWED_HOSTS:** Ya es dinámico en ambas ramas. No necesita cambio.

**Edición C — Disable Browsable API.** Agregar inmediatamente DESPUÉS del bloque `REST_FRAMEWORK = { ... }`:
```python
# Disable Browsable API in production (security: prevents endpoint/model exposure)
if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
    )
```

> **NOTA importante para users-service:** `develop` tenía `ROTATE_REFRESH_TOKENS: True`. El bugfix lo cambió deliberadamente a `False`. **Mantener `False`** — es una decisión del bugfix para evitar race conditions en el refresh vía cookies.

**Edición D — Security hardening.** Agregar AL FINAL del archivo:
```python
# =============================================================================
# Security hardening (production)
# =============================================================================
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
```

---

## Fase 3 — Commit

```bash
git add -A
git commit -m "fix: resolve merge conflicts — keep cookie auth + restore production hardening"
git push origin fix/bug-httponly-cookies
```

---

## Checklist de Validación Final

Ejecutar estas verificaciones antes del commit:

### Sin marcadores de conflicto residuales
```bash
git diff --check
grep -rn "<<<<<<\|======\|>>>>>>" backend/ frontend/ --include="*.py" --include="*.ts" --include="*.tsx"
```
Debe retornar vacío.

### Backend — Autenticación correcta
```bash
grep -n "DEFAULT_AUTHENTICATION_CLASSES" backend/*/assessment_service/settings.py backend/*/notification_service/settings.py backend/*/ticket_service/settings.py backend/*/user_service/settings.py
```
Debe mostrar:
- assignment-service: `assignments.infrastructure.cookie_auth.CookieJWTStatelessAuthentication`
- notification-service: `notifications.infrastructure.cookie_auth.CookieJWTStatelessAuthentication`
- ticket-service: `tickets.infrastructure.cookie_auth.CookieJWTStatelessAuthentication`
- users-service: `users.infrastructure.cookie_authentication.CookieJWTAuthentication`

### Backend — Cookie credentials habilitadas
```bash
grep -n "CORS_ALLOW_CREDENTIALS" backend/*/assessment_service/settings.py backend/*/notification_service/settings.py backend/*/ticket_service/settings.py backend/*/user_service/settings.py
```
Debe mostrar `True` en los 4 servicios.

### Backend — DEBUG default es false
```bash
grep -n 'DJANGO_DEBUG' backend/*/assessment_service/settings.py backend/*/notification_service/settings.py backend/*/ticket_service/settings.py backend/*/user_service/settings.py
```
Debe mostrar `"false"` como default en los 4 servicios.

### Backend — Security hardening presente
```bash
grep -n "SECURE_BROWSER_XSS_FILTER" backend/*/assessment_service/settings.py backend/*/notification_service/settings.py backend/*/ticket_service/settings.py backend/*/user_service/settings.py
```
Debe retornar 4 coincidencias.

### Frontend — Sin localStorage para auth
```bash
grep -rn "localStorage" frontend/src/components/ProtectedRoute.tsx frontend/src/pages/navbar/NavBar.tsx frontend/src/pages/tickets/TicketList.tsx frontend/src/pages/assignments/AssignmentList.tsx frontend/src/services/ticketApi.ts
```
Debe retornar vacío.

### Frontend — Sin authService en componentes migrados
```bash
grep -rn "authService" frontend/src/components/ProtectedRoute.tsx frontend/src/pages/navbar/NavBar.tsx frontend/src/pages/tickets/TicketList.tsx frontend/src/pages/assignments/AssignmentList.tsx
```
Debe retornar vacío.

---

## Qué NO Tocar

| Elemento | Razón |
|----------|-------|
| `ROTATE_REFRESH_TOKENS: False` (users-service) | Decisión deliberada del bugfix para evitar race conditions en cookie refresh |
| Imports de `useAuth` en componentes frontend | Son el reemplazo de `authService` — core del bugfix |
| `CookieJWT*Authentication` classes | Nuevas clases de auth — no revertir a `JWTStatelessUserAuthentication` |
| `CORS_ALLOW_CREDENTIALS = True` | Requerido para que el navegador envíe cookies cross-origin |
| `CSRF_TRUSTED_ORIGINS` | Requerido cuando `CORS_ALLOW_CREDENTIALS = True` |
| Parámetro `adminId` explícito en `ticketApi.createResponse` | Reemplaza lectura de localStorage — es el fix de la vulnerabilidad |

---

## Limpieza Post-Merge

Tras confirmar que el PR mergea limpiamente, eliminar del repo:
- `ORCHESTRATOR_PROMPT.md`
- `MERGE_CONFLICT_RESOLUTION.md`

Estos archivos son temporales y no deben llegar a `develop`.
