# Notification Service

Microservicio de notificaciones implementado con **Django REST Framework** y arquitectura **DDD + EDA**.

## Descripción

Este servicio escucha eventos `ticket_created` en RabbitMQ y gestiona notificaciones en PostgreSQL.

### Funcionalidades

- ✅ Crear notificaciones desde eventos RabbitMQ
- ✅ Consultar notificaciones (CRUD completo)
- ✅ Marcar notificaciones como leídas (idempotente)
- ✅ Publicar eventos de dominio (EDA)

## Arquitectura

El servicio sigue **Domain-Driven Design (DDD)** con arquitectura en capas:

```
notifications/
├── domain/           → Reglas de negocio puras
├── application/      → Casos de uso (orquestación)
├── infrastructure/   → Adaptadores (Django, RabbitMQ)
├── tests/            → Tests organizados por capa
├── api.py            → ViewSet (thin controller)
├── models.py         → Modelo Django (persistencia)
└── serializers.py    → Serializers DRF
```

### Documentación

- **[ARCHITECTURE_DDD.md](ARCHITECTURE_DDD.md)** - Arquitectura completa explicada
- **[QUICK_START_DDD.md](QUICK_START_DDD.md)** - Guía rápida para desarrolladores
- **[BEFORE_AFTER.md](BEFORE_AFTER.md)** - Comparación antes/después de la refactorización

## Ejecución Local

### Con Docker Compose

```bash
# Build del servicio
docker compose build notification-service

# Levantar dependencias
docker compose up -d db rabbitmq

# Levantar notification-service
docker compose up notification-service
```

### Testing

```bash
# Todos los tests
python manage.py test notifications.tests

# Tests por capa
python manage.py test notifications.tests.test_domain          # Dominio (rápidos)
python manage.py test notifications.tests.test_use_cases       # Casos de uso
python manage.py test notifications.tests.test_infrastructure  # Repositorio
python manage.py test notifications.tests.test_views           # ViewSet
python manage.py test notifications.tests.test_integration     # Integración
```

## API Endpoints

### Listar Notificaciones
```http
GET /api/notifications/
```

### Obtener Notificación
```http
GET /api/notifications/{id}/
```

### Crear Notificación
```http
POST /api/notifications/
Content-Type: application/json

{
  "ticket_id": "T-123",
  "message": "Ticket creado"
}
```

### Marcar como Leída
```http
PATCH /api/notifications/{id}/read/
```

**Respuesta:** `204 No Content`

**Idempotente:** Llamadas múltiples no generan efectos secundarios.

## Características Técnicas

### Reglas de Negocio

- **Idempotencia:** Marcar como leída múltiples veces no genera errores
- **Domain Events:** Cada cambio importante genera eventos
- **Validación:** Reglas de negocio encapsuladas en entidades

### Patrones Aplicados

- **Entity:** `Notification` con reglas de negocio
- **Repository:** Abstracción de persistencia (DIP)
- **Use Case:** Orquestación de operaciones
- **Adapter:** Django ORM, RabbitMQ
- **Domain Events:** Comunicación asíncrona

### Principios SOLID

- ✅ **SRP:** Cada clase con una responsabilidad
- ✅ **OCP:** Abierto a extensión, cerrado a modificación
- ✅ **LSP:** Entidades sustituibles
- ✅ **ISP:** Interfaces específicas
- ✅ **DIP:** Dependencias invertidas

## Desarrollo

### Agregar Nuevo Caso de Uso

1. Crear comando en `application/use_cases.py`
2. Implementar caso de uso
3. Agregar método al repositorio si es necesario
4. Usar en `api.py`
5. Escribir tests

Ver [QUICK_START_DDD.md](QUICK_START_DDD.md) para ejemplos.

### Testing

Pirámide de tests:

```
     /\
    /E2E\         ← Pocos, lentos
   /------\
  /  API  \       ← Algunos
 /----------\
/ Unit Tests \    ← Muchos, rápidos
```

## Tecnologías

- **Python 3.10+**
- **Django 4.2+**
- **Django REST Framework 3.14+**
- **PostgreSQL 13+**
- **RabbitMQ 3.11+**
- **pika** (cliente RabbitMQ)

## Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@db:5432/notifications

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_EXCHANGE_NAME=notifications

# Django
DEBUG=True
SECRET_KEY=your-secret-key
```

## Compatibilidad

✅ **100% compatible con versión anterior**
- Mismos endpoints
- Mismos contratos HTTP
- Sin breaking changes

## Contribuir

1. Leer [ARCHITECTURE_DDD.md](ARCHITECTURE_DDD.md)
2. Seguir estructura de capas
3. Escribir tests
4. Mantener reglas de negocio en dominio
5. ViewSets como thin controllers

## Licencia

Proyecto académico - FinalFinal Sistema de Tickets

