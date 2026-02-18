# Project Copilot Instructions — Ticket Microservices System

## Architecture Overview

This repository implements a microservices-based ticketing system composed of:

- **Ticket Service** (backend/ticket-service): Gestión de tickets y estados. Referencia DDD.
- **Assignment Service** (backend/assignment-service): Asignación de tickets a agentes.
- **Notification Service** (backend/notification-service): Gestión de notificaciones.
- **User Service** (backend/users-service): Usuarios y autenticación.
- **Frontend** (frontend/): SPA React + TypeScript.

**Stack:** Django 5.x, DRF, RabbitMQ (Pika), PostgreSQL 16, React 19, Vite, Vitest. Testing backend: Pytest.

Ticket Service follows Domain Driven Design (DDD).
Other services are being progressively aligned to this architecture.

When generating code:

- NEVER couple services via database imports
- ALWAYS communicate via REST API or domain events
- Prefer event-driven integration over synchronous coupling

---

## Business Rules (Reglas de Negocio)

### Tickets (Ticket Service)
- **Estados válidos:** `OPEN`, `IN_PROGRESS`, `CLOSED` (transición: OPEN → IN_PROGRESS → CLOSED)
- **Regla:** Un ticket en estado `CLOSED` NO puede cambiar de estado → lanzar excepción de dominio `TicketAlreadyClosed`
- **Creación:** Ticket nuevo siempre inicia en `OPEN`. Título y descripción obligatorios.
- **Eventos:** Tras crear ticket → publicar `ticket.created`; tras cambio de estado válido → publicar `ticket.status_changed` (ver esquemas abajo)
- **Idempotencia:** Si el ticket ya tiene el estado solicitado, no hacer cambio ni publicar evento

**Contratos de eventos (mantener compatibilidad):**

`ticket.created`:
```json
{ "event_type": "ticket.created", "ticket_id": int, "title": str, "user_id": int, "status": "open", "timestamp": "ISO8601" }
```

`ticket.status_changed`:
```json
{ "event_type": "ticket.status_changed", "ticket_id": int, "old_status": str, "new_status": str, "timestamp": "ISO8601" }
```

### Asignación (Assignment Service)
- **Regla:** Al recibir evento `ticket.created`, asignar un agente al ticket
- **Prioridad:** Actualmente lógica placeholder (aleatoria). Al evolucionar, usar reglas de negocio (carga, SLA, roles) en capa de dominio, no en handler

### Notificaciones (Notification Service)
- **Regla:** Al recibir `ticket.created` (y otros eventos definidos), crear notificación correspondiente y persistirla
- **Responsabilidad:** La regla de qué notificar vive en dominio; el handler solo orquesta

### Usuarios (User Service)
- **Roles:** Usuario estándar vs agente
- **Comunicación:** Otros servicios NO deben importar modelos de User Service ni acceder a `users_db`. Usar API REST o eventos
- **Objetivo:** User Service aún no publica eventos; al integrarlo en EDA, emitir eventos ante cambios de usuario/rol

### Referencias de documentación
- Reglas detalladas y riesgos: [HANDOVER_REPORT.md](HANDOVER_REPORT.md), [AUDITORIA.md](AUDITORIA.md), [DEUDA_TECNICA.md](DEUDA_TECNICA.md), [CALIDAD.md](CALIDAD.md)
- Arquitectura DDD por servicio: `backend/ticket-service/ARCHITECTURE_DDD.md`

---

# Coding Philosophy

## Type Hints
- **Ticket Service:** 100% type hints (mantener).
- **Assignment, Notification, User Services:** Extender type hints en código nuevo. Priorizar dominio y casos de uso.
- Usar anotaciones en funciones públicas y constructores.

## Clean Architecture Priority

Always respect layer separation:

Domain → Application → Infrastructure → Presentation

Rules:

- Domain must be pure Python (no Django imports)
- Business logic must NOT exist in Django Views
- Messaging handlers must delegate to Use Cases
- ORM models belong ONLY to infrastructure


---

# Naming Conventions

## Python

- Classes → PascalCase
- Functions → snake_case
- Variables → snake_case
- Constants → UPPER_CASE

## TypeScript / React

- Components → PascalCase
- Hooks → camelCase
- Variables → camelCase


---

# Error Handling Rules

## Backend

- Wrap RabbitMQ consumers in try/except
- Never crash consumer loop
- Always log structured errors

## Frontend

- Always use global error boundaries
- Handle API failures explicitly
- Never silently ignore HTTP errors


---

# RabbitMQ Rules

- Events must include: `event_type`, `timestamp`, payload object (ver contratos en Business Rules)
- Consumers must be idempotent
- Never assume message delivery exactly once
- Support reconnection logic
- **Reducción de duplicación:** ~90% del setup de consumidores se duplica entre Assignment y Notification. Al refactorizar, considerar abstracción común (ej. `BaseRabbitMQConsumer`) para evitar código duplicado


---

# Database Rules

STRICT RULE:

❌ NEVER import models from another microservice  
❌ NEVER connect to another service DB  

✔ Use REST API  
✔ Use events  

This is mandatory.


---

# Testing Standards

Backend:

- Unit tests for domain logic required
- Avoid Django dependency in domain tests

Frontend:

- Use Vitest + React Testing Library
- Test behavior, not implementation


---

# Security Standards

Frontend:

- Never store auth tokens in localStorage
- Prefer HttpOnly cookies strategy

Backend:

- Secrets must come from environment variables
- Never hardcode credentials


---

# Documentation Standards

When generating code:

- Add docstrings to public Python functions
- Add JSDoc for exported TypeScript functions
- Explain event payload structures

Focus on clarity over verbosity.

---


