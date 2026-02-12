# Pruebas de Endpoints - Users Service

El servicio está corriendo en: `http://localhost:8003`

## 1. Health Check

```bash
curl http://localhost:8003/api/health/
```

**Respuesta esperada:**
```json
{
  "service": "users-service",
  "status": "healthy",
  "database": "connected"
}
```

## 2. Registro de Usuario (USER role por defecto)

```bash
curl -X POST http://localhost:8003/api/auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "usuario1",
    "password": "password123"
  }'
```

**Respuesta esperada:**
```json
{
  "id": "uuid-generado",
  "email": "user@example.com",
  "username": "usuario1",
  "role": "USER",
  "is_active": true,
  "created_at": "2026-02-12T..."
}
```

## 3. Registro de Usuario con role ADMIN

```bash
curl -X POST http://localhost:8003/api/auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin1",
    "password": "password123",
    "role": "ADMIN"
  }'
```

**Respuesta esperada:**
```json
{
  "id": "uuid-generado",
  "email": "admin@example.com",
  "username": "admin1",
  "role": "ADMIN",
  "is_active": true,
  "created_at": "2026-02-12T..."
}
```

## 4. Login de Usuario

```bash
curl -X POST http://localhost:8003/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**Respuesta esperada:**
```json
{
  "id": "uuid-del-usuario",
  "email": "user@example.com",
  "username": "usuario1",
  "role": "USER",
  "is_active": true,
  "created_at": "2026-02-12T..."
}
```

## 5. Login con credenciales inválidas

```bash
curl -X POST http://localhost:8003/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "wrongpassword"
  }'
```

**Respuesta esperada:**
```json
{
  "error": "Credenciales inválidas"
}
```
Status: 401 Unauthorized

## Notas

- El password se hashea automáticamente usando SHA-256 (en producción usar bcrypt)
- El role por defecto es "USER"
- Los roles disponibles son: "ADMIN" y "USER"
- La respuesta del login incluye el role del usuario para diferenciación en el frontend
- No implementamos autorización todavía, solo autenticación y diferenciación de roles
