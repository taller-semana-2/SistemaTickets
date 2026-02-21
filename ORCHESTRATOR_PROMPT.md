# Prompt Principal — Orchestrator

> **Contexto:** El PR #109 (`fix/bug-httponly-cookies` → `develop`) en `taller-semana-2/SistemaTickets` tiene 9 archivos en conflicto. Este PR migra la autenticación de `localStorage` a HttpOnly cookies y es un **bugfix de seguridad crítico**. Los cambios de este branch deben prevalecer, con re-inyección quirúrgica de mejoras de producción que `develop` agregó.

---

## Tu Misión

Coordinar la resolución de los 9 conflictos de merge del PR #109, delegando al **Coder** la ejecución de los cambios. El archivo `MERGE_CONFLICT_RESOLUTION.md` (en la raíz del repo) contiene las instrucciones detalladas archivo por archivo.

---

## Secuencia de Trabajo

### Fase 0 — Pre-requisito (Humano)

Antes de que puedas actuar, el humano debe ejecutar en terminal:

```bash
cd <ruta-del-repo>
git checkout fix/bug-httponly-cookies
git fetch origin
git merge origin/develop
```

Esto generará los 9 conflictos. A partir de ahí, los agentes trabajan.

---

### Fase 1 — Frontend (5 archivos) → Coder

**Estrategia: "Take Ours" al 100%.** Sin excepciones.

Indicar al Coder que resuelva estos 5 archivos aceptando la versión completa de `fix/bug-httponly-cookies` (ours). No se necesita merge manual ni edición adicional.

Archivos:
1. `frontend/src/components/ProtectedRoute.tsx`
2. `frontend/src/pages/assignments/AssignmentList.tsx`
3. `frontend/src/pages/navbar/NavBar.tsx`
4. `frontend/src/pages/tickets/TicketList.tsx`
5. `frontend/src/services/ticketApi.ts`

**Comando rápido:**
```bash
git checkout --ours frontend/src/components/ProtectedRoute.tsx
git checkout --ours frontend/src/pages/assignments/AssignmentList.tsx
git checkout --ours frontend/src/pages/navbar/NavBar.tsx
git checkout --ours frontend/src/pages/tickets/TicketList.tsx
git checkout --ours frontend/src/services/ticketApi.ts
git add frontend/src/components/ProtectedRoute.tsx \
       frontend/src/pages/assignments/AssignmentList.tsx \
       frontend/src/pages/navbar/NavBar.tsx \
       frontend/src/pages/tickets/TicketList.tsx \
       frontend/src/services/ticketApi.ts
```

**Validación Fase 1:** Verificar que ningún archivo frontend contiene `<<<<<<`, `======`, `>>>>>>`. Verificar que ninguno importa `authService` ni `getAccessToken` desde `services/auth`.

---

### Fase 2 — Backend Settings (4 archivos) → Coder

**Estrategia: "Take Ours" + re-inyectar bloques de hardening de develop.**

Primero resolver con ours:
```bash
git checkout --ours backend/assignment-service/assessment_service/settings.py
git checkout --ours backend/notification-service/notification_service/settings.py
git checkout --ours backend/ticket-service/ticket_service/settings.py
git checkout --ours backend/users-service/user_service/settings.py
git add backend/assignment-service/assessment_service/settings.py \
       backend/notification-service/notification_service/settings.py \
       backend/ticket-service/ticket_service/settings.py \
       backend/users-service/user_service/settings.py
```

Luego aplicar las 4 ediciones descritas en `MERGE_CONFLICT_RESOLUTION.md` sección "Fase 2" sobre cada archivo.

**Validación Fase 2:**
- Cada `settings.py` debe tener `CookieJWT*Authentication` (NO `JWTStatelessUserAuthentication`)
- Cada `settings.py` debe tener `CORS_ALLOW_CREDENTIALS = True`
- Cada `settings.py` debe tener `CSRF_TRUSTED_ORIGINS`
- Cada `settings.py` debe tener `DEBUG` default `"false"`
- Cada `settings.py` debe tener `ALLOWED_HOSTS` dinámico desde env
- Los 3 consumer services deben tener el bloque `if not DEBUG: DEFAULT_RENDERER_CLASSES`
- Los 4 servicios deben tener el bloque de security hardening al final

---

### Fase 3 — Commit & Push (Humano o Coder)

```bash
git commit -m "fix: resolve merge conflicts — keep cookie auth + restore production hardening"
git push origin fix/bug-httponly-cookies
```

---

### Fase 4 — Verificación Post-Merge (Humano)

El humano debe:
1. Revisar el PR #109 en GitHub — verificar que `mergeable_state` ya no es `dirty`
2. Hacer un `docker-compose up --build` y verificar que los 4 servicios arrancan
3. Probar login → verificar que se setean HttpOnly cookies (no localStorage)
4. Verificar que la Browsable API de DRF NO aparece en producción (`DEBUG=false`)

---

## Reglas para el Orchestrator

1. **No modificar la lógica de autenticación por cookies.** Es el core del bugfix.
2. **No reintroducir `localStorage`** ni `authService.getCurrentUser()` en frontend.
3. **No cambiar `ROTATE_REFRESH_TOKENS: False`** en users-service (decisión deliberada del bugfix).
4. Las ediciones de hardening son **aditivas** — no reemplazan nada del bugfix, solo agregan.
5. Si un agente tiene duda, la respuesta por defecto es **preservar la versión del bugfix**.

---

## Archivos de Referencia

- Instrucciones detalladas: `MERGE_CONFLICT_RESOLUTION.md`
- PR original: https://github.com/taller-semana-2/SistemaTickets/pull/109

---

> **Tras completar la resolución, eliminar este archivo y `MERGE_CONFLICT_RESOLUTION.md` del repo.** Son temporales.
