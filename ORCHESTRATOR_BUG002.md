# ORCHESTRATOR_BUG002 — Instrucciones para resolver BUG-002

## Issue de referencia
- **GitHub Issue:** [#56 — Escalamiento de privilegios: cualquiera puede registrarse como ADMIN](https://github.com/taller-semana-2/SistemaTickets/issues/56)
- **Branch de trabajo:** `fix/bug-002-privilege-escalation`
- **Severidad:** Crítica (Seguridad)

---

## 1. Contexto del Bug

El endpoint público de registro (`POST /api/auth/`) acepta un campo `role` en el body de la petición. Cualquier atacante puede enviar `"role": "ADMIN"` y crear una cuenta con privilegios de administrador, obteniendo control total del sistema.

### Flujo actual (vulnerable):
```
Cliente → POST /api/auth/ { role: "ADMIN" }
  → RegisterUserSerializer (acepta role como ChoiceField)
    → views.py create() (pasa role al command)
      → RegisterUserCommand(role="ADMIN")
        → RegisterUserUseCase (propaga role al factory)
          → UserFactory.create(role=UserRole.ADMIN)
            → Usuario creado como ADMIN ❌
```

### Flujo esperado (corregido):
```
Cliente → POST /api/auth/ { role: "ADMIN" }
  → RegisterUserSerializer (NO acepta role / lo ignora)
    → views.py create() (NO pasa role)
      → RegisterUserCommand() (sin role)
        → RegisterUserUseCase (fuerza UserRole.USER)
          → UserFactory.create(role=UserRole.USER)
            → Usuario creado como USER ✅
```

---

## 2. Archivos afectados y cambios requeridos

### 2.1 Backend — `users-service`

| Archivo | Líneas | Cambio requerido |
|---------|--------|------------------|
| `backend/users-service/users/serializers.py` | 48-52 | **Eliminar** el campo `role` de `RegisterUserSerializer` |
| `backend/users-service/users/views.py` | 227 | **Eliminar** la lectura de `role` de `validated_data`; no pasarlo al command |
| `backend/users-service/users/application/use_cases.py` | 63-66 | **Eliminar** el parámetro `role` de `RegisterUserCommand` |
| `backend/users-service/users/application/use_cases.py` | 367-372 | **Forzar** `UserRole.USER` en `RegisterUserUseCase.execute()`, ignorar cualquier role del command |

### 2.2 Frontend

| Archivo | Línea | Cambio requerido |
|---------|-------|------------------|
| `frontend/src/types/auth.ts` | 21 | **Eliminar** `role?: UserRole` de `RegisterRequest` |

---

## 3. Prompts por Agente

### 3.1 Prompt para Planner

```
Contexto: Estamos resolviendo el Issue #56 (BUG-002) — Escalamiento de privilegios en el registro de usuarios. El endpoint POST /api/auth/ acepta un campo "role" que permite a cualquier usuario registrarse como ADMIN.

Necesito que planifiques las tareas necesarias para resolver este bug, siguiendo estas restricciones:
1. Respetar la arquitectura DDD del users-service (Domain → Application → Infrastructure → Presentation)
2. La validación DEBE ser server-side (no depender del frontend)
3. La corrección del frontend es defensa en profundidad, no la solución principal
4. No romper la funcionalidad de registro existente
5. Incluir tests unitarios de dominio y tests de integración

Branch de trabajo: fix/bug-002-privilege-escalation

Archivos a modificar:
- backend/users-service/users/serializers.py (eliminar campo role de RegisterUserSerializer)
- backend/users-service/users/views.py (no pasar role al command)
- backend/users-service/users/application/use_cases.py (eliminar role de RegisterUserCommand, forzar USER en use case)
- frontend/src/types/auth.ts (eliminar role de RegisterRequest)

Archivos de test a crear/modificar:
- backend/users-service/users/tests.py o backend/users-service/users/tests/ (tests de integración del endpoint)
- backend/users-service/users/domain/test_entities.py (test unitario de dominio)
- backend/users-service/users/application/test_use_cases.py (test unitario de use case)

Planifica las tareas en orden de ejecución con dependencias claras.
```

---

### 3.2 Prompt para Coder (Backend)

````
Contexto: Estás resolviendo el Issue #56 (BUG-002) — Escalamiento de privilegios en registro de usuarios.
Branch: fix/bug-002-privilege-escalation
Repositorio: taller-semana-2/SistemaTickets

## Problema
El RegisterUserSerializer acepta un campo `role` que permite a cualquiera registrarse como ADMIN.

## Cambios requeridos (en este orden):

### Paso 1: Serializer — Eliminar campo role
Archivo: backend/users-service/users/serializers.py

ANTES (líneas 48-52):
```python
class RegisterUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(min_length=3, max_length=50, required=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    role = serializers.ChoiceField(
        choices=['ADMIN', 'USER'],
        default='USER',
        required=False
    )
```

DESPUÉS:
```python
class RegisterUserSerializer(serializers.Serializer):
    """Serializer para registrar un nuevo usuario (INPUT).
    
    SEGURIDAD: No se acepta campo 'role'. Todo registro público
    crea usuarios con rol USER. El rol solo puede ser asignado
    por un administrador autenticado.
    """
    email = serializers.EmailField(required=True)
    username = serializers.CharField(min_length=3, max_length=50, required=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)
```

### Paso 2: Vista — No pasar role al command
Archivo: backend/users-service/users/views.py

ANTES (línea 227):
```python
command = RegisterUserCommand(
    email=serializer.validated_data['email'],
    username=serializer.validated_data['username'],
    password=serializer.validated_data['password'],
    role=serializer.validated_data.get('role', 'USER')
)
```

DESPUÉS:
```python
command = RegisterUserCommand(
    email=serializer.validated_data['email'],
    username=serializer.validated_data['username'],
    password=serializer.validated_data['password'],
)
```

### Paso 3: Command — Eliminar parámetro role
Archivo: backend/users-service/users/application/use_cases.py

ANTES (líneas 63-66):
```python
@dataclass
class RegisterUserCommand:
    """Comando: Registrar un nuevo usuario."""
    email: str
    username: str
    password: str
    role: str = "USER"
```

DESPUÉS:
```python
@dataclass
class RegisterUserCommand:
    """Comando: Registrar un nuevo usuario.
    
    SEGURIDAD: No incluye campo 'role'. El registro público
    siempre crea usuarios con rol USER.
    """
    email: str
    username: str
    password: str
```

### Paso 4: Use Case — Forzar UserRole.USER
Archivo: backend/users-service/users/application/use_cases.py

ANTES (en RegisterUserUseCase.execute, líneas ~367-372):
```python
# 2. Convertir string role a enum
role = UserRole(command.role)

# 3. Crear entidad de dominio usando factory (valida)
user = self.factory.create(
    email=command.email,
    username=command.username,
    password=command.password,
    role=role
)
```

DESPUÉS:
```python
# 2. Crear entidad de dominio usando factory (valida)
# SEGURIDAD: Siempre forzar UserRole.USER en registro público
user = self.factory.create(
    email=command.email,
    username=command.username,
    password=command.password,
    role=UserRole.USER
)
```

## Reglas de código:
- Mantener type hints 100%
- Mantener docstrings en funciones públicas
- No importar Django en capa de dominio
- Usar Conventional Commits: `fix(users): prevent privilege escalation in registration endpoint`
- Incluir `Closes #56` en el commit message

## Tests requeridos (Paso 5):

### Test de integración del endpoint:
```python
# En tests.py o test_views.py
def test_register_ignores_role_field():
    """Verifica que el campo role es ignorado en registro público."""
    response = client.post('/api/auth/', {
        'email': 'test@test.com',
        'username': 'testuser',
        'password': 'password123',
        'role': 'ADMIN'
    })
    assert response.status_code == 201
    assert response.data['user']['role'] == 'USER'

def test_register_creates_user_role():
    """Verifica que el registro siempre crea usuario con rol USER."""
    response = client.post('/api/auth/', {
        'email': 'test2@test.com',
        'username': 'testuser2',
        'password': 'password123',
    })
    assert response.status_code == 201
    assert response.data['user']['role'] == 'USER'
```

### Test unitario del use case:
```python
def test_register_use_case_forces_user_role():
    """Verifica que RegisterUserUseCase siempre crea con UserRole.USER."""
    command = RegisterUserCommand(
        email='test@test.com',
        username='testuser',
        password='password123',
    )
    # ... mock repository y event_publisher
    result = use_case.execute(command)
    assert result['user'].role == UserRole.USER
```
````

---

### 3.3 Prompt para Coder (Frontend)

````
Contexto: Estás resolviendo el Issue #56 (BUG-002) — Parte frontend.
Branch: fix/bug-002-privilege-escalation
Repositorio: taller-semana-2/SistemaTickets

## Problema
El tipo RegisterRequest incluye `role?: UserRole` que no debería existir en el registro público.

## Cambio requerido:

Archivo: frontend/src/types/auth.ts

ANTES (línea 17-22):
```typescript
export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  role?: UserRole;
}
```

DESPUÉS:
```typescript
export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}
```

## Verificaciones:
1. Confirmar que el componente Register.tsx NO envía campo role (actualmente no lo hace — solo envía username, email, password)
2. Confirmar que authService.register() no agrega role al body
3. No se requieren cambios en Register.tsx ni en auth.ts (solo el tipo)

## Test sugerido (Vitest):
```typescript
// Verificar que el formulario de registro no envía campo role
it('should not include role in registration request', async () => {
  // ... mock axios
  await authService.register({
    email: 'test@test.com',
    username: 'testuser',
    password: 'password123',
  });
  expect(axiosPostSpy).toHaveBeenCalledWith('/auth/', {
    email: 'test@test.com',
    username: 'testuser',
    password: 'password123',
  });
  // Verify no 'role' key in the request body
});
```

## Reglas:
- Usar Conventional Commits: `fix(frontend): remove role field from RegisterRequest type`
- TypeScript strict mode
- No almacenar datos sensibles en localStorage (ya es tech debt documentado)
````

---

### 3.4 Prompt para Designer (si aplica)

```
Contexto: BUG-002 no requiere cambios de UI. El formulario de registro actual
(frontend/src/pages/auth/Register.tsx) ya NO muestra selector de rol.

Verificación requerida:
1. Confirmar que la página de registro (/register) no tiene campo de selección de rol
2. Confirmar que no hay forma visual de seleccionar ADMIN durante el registro
3. No se requieren cambios de diseño

Si en el futuro se necesita una interfaz para que administradores asignen roles,
esa sería una feature separada (no parte de este bug fix).
```

---

## 4. Prompt para el Orchestrator (Prompt Principal)

```
# Contexto
Estamos resolviendo el Issue #56 del repositorio taller-semana-2/SistemaTickets:
BUG-002 — Escalamiento de privilegios: cualquiera puede registrarse como ADMIN.

El endpoint público POST /api/auth/ acepta un campo "role" en el body, permitiendo
que cualquier atacante se registre como ADMIN. Es una vulnerabilidad CRÍTICA de seguridad.

# Objetivo
Corregir el bug eliminando la posibilidad de asignar roles durante el registro público.
Todo usuario registrado por el endpoint público DEBE tener rol USER.

# Branch de trabajo
fix/bug-002-privilege-escalation (crear desde main si no existe)

# Plan de ejecución

## Fase 1: Backend (Coder Backend) — PRIORIDAD MÁXIMA
La solución principal es server-side. Ejecutar en este orden:

1. **Serializer**: Eliminar campo `role` de `RegisterUserSerializer`
   - Archivo: backend/users-service/users/serializers.py
   
2. **Vista**: Eliminar lectura de `role` de validated_data en create()
   - Archivo: backend/users-service/users/views.py
   
3. **Command**: Eliminar parámetro `role` de `RegisterUserCommand`
   - Archivo: backend/users-service/users/application/use_cases.py
   
4. **Use Case**: Forzar `UserRole.USER` en `RegisterUserUseCase.execute()` 
   - Archivo: backend/users-service/users/application/use_cases.py

5. **Tests**: Crear tests de integración y unitarios que verifiquen:
   - Enviar role=ADMIN en registro → usuario creado como USER
   - Registro sin role → usuario creado como USER
   - Use case siempre fuerza UserRole.USER

## Fase 2: Frontend (Coder Frontend) — Defensa en profundidad
6. **Tipo**: Eliminar `role?: UserRole` de `RegisterRequest`
   - Archivo: frontend/src/types/auth.ts
   
7. **Verificar**: Que Register.tsx y authService.register() no envían role
   (actualmente no lo hacen, pero verificar)

## Fase 3: Design Review (Designer)
8. Confirmar que la UI de registro no expone selector de rol

## Fase 4: Validación
9. Ejecutar tests: `cd backend/users-service && python -m pytest`
10. Ejecutar tests frontend: `cd frontend && npm run test`
11. Test manual: Intentar registrarse con role=ADMIN via cURL y verificar que se crea como USER

# Restricciones
- Respetar DDD: Domain (puro Python) → Application → Infrastructure → Presentation
- No importar Django en capa de dominio
- No acoplar servicios vía imports entre microservicios
- La validación DEBE ser server-side (el frontend es defensa en profundidad)
- Conventional Commits obligatorio
- El PR debe incluir `Closes #56`
- Pasar por Quality Gate (AI_WORKFLOW.md) antes del commit

# Criterios de aceptación verificables
- [ ] POST /api/auth/ con role=ADMIN → crea usuario con role USER
- [ ] POST /api/auth/ sin role → crea usuario con role USER
- [ ] RegisterUserSerializer no acepta campo role
- [ ] RegisterUserCommand no tiene parámetro role
- [ ] RegisterUserUseCase fuerza UserRole.USER
- [ ] RegisterRequest (frontend) no incluye campo role
- [ ] Tests unitarios y de integración pasan
- [ ] Funcionalidad de registro normal no se rompe
- [ ] Login de usuarios existentes no se afecta
```

---

## 5. Checklist de Validación Post-Fix

- [ ] `POST /api/auth/` con `"role": "ADMIN"` → respuesta con `"role": "USER"`
- [ ] `POST /api/auth/` sin campo `role` → respuesta con `"role": "USER"`
- [ ] `GET /api/auth/by-role/ADMIN/` no muestra usuarios creados por registro público
- [ ] El formulario de registro del frontend sigue funcionando correctamente
- [ ] Login de usuarios existentes no se ve afectado
- [ ] Tests backend pasan (`python -m pytest`)
- [ ] Tests frontend pasan (`npm run test`)
- [ ] No hay regresiones en otros servicios (ticket, assignment, notification)
- [ ] Branch `fix/bug-002-privilege-escalation` tiene PR hacia `main` con `Closes #56`
- [ ] Commits siguen Conventional Commits

---

## 6. Notas de Arquitectura

### Por qué la corrección va en múltiples capas (defensa en profundidad):

| Capa | Cambio | Razón |
|------|--------|-------|
| **Serializer** (Presentación) | Eliminar campo `role` | Primera línea de defensa: no aceptar el dato |
| **Command** (Aplicación) | Eliminar parámetro `role` | No propagar datos peligrosos entre capas |
| **Use Case** (Aplicación) | Forzar `UserRole.USER` | Garantía final: la lógica de negocio decide el rol |
| **Frontend** (Tipo TS) | Eliminar `role` del tipo | Defensa en profundidad client-side |

### Qué NO cambiar:
- `UserFactory.create()` — Sigue aceptando `role` como parámetro, ya que podría usarse internamente por un futuro endpoint administrativo
- `User` entity — No necesita cambio, la entidad de dominio está correcta
- `UserRole` enum — No necesita cambio
- Otros serializers (`UserResponseSerializer`, `AuthUserSerializer`) — Siguen mostrando `role` en el output, lo cual es correcto
