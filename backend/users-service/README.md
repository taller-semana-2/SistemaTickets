# Users Service 👥

Microservicio de gestión de usuarios construido con Django + DDD + EDA.

## 🏗️ Arquitectura

Este servicio implementa **Domain-Driven Design (DDD)** ligero + **Event-Driven Architecture (EDA)**:

- **Dominio puro**: Sin dependencias de frameworks
- **Casos de uso**: Orquestación de lógica de negocio
- **Repositorios**: Abstracción de persistencia
- **Eventos**: Comunicación asíncrona con otros servicios

Ver [ARCHITECTURE_DDD.md](./ARCHITECTURE_DDD.md) para detalles completos.

## 📁 Estructura del Proyecto

```
users-service/
├── manage.py                 # CLI de Django
├── requirements.txt          # Dependencias Python
├── user_service/            # Configuración del proyecto Django
│   ├── settings.py          # Configuración principal
│   ├── urls.py              # URLs raíz
│   ├── wsgi.py              # Servidor WSGI
│   └── asgi.py              # Servidor ASGI
│
└── users/                   # Aplicación principal
    ├── domain/              # Lógica de negocio pura
    ├── application/         # Casos de uso
    ├── infrastructure/      # Adaptadores (Django ORM, RabbitMQ)
    ├── messaging/           # Consumidores de eventos
    ├── tests/               # Tests organizados por capa
    ├── views.py             # Controladores HTTP (ViewSets)
    ├── serializers.py       # Serialización JSON
    ├── urls.py              # URLs de la API
    └── models.py            # Modelos Django ORM
```

## 🚀 Quick Start

### 1. Crear y activar entorno virtual

```powershell
# Windows PowerShell
cd backend/users-service
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Ejecutar migraciones

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 4. Crear superusuario (opcional)

```powershell
python manage.py createsuperuser
```

### 5. Ejecutar servidor de desarrollo

```powershell
python manage.py runserver 8001
```

El servicio estará disponible en: `http://localhost:8001`

## 📡 API Endpoints

Una vez implementados los casos de uso, el servicio expondrá:

```
POST   /api/users/                    # Crear usuario
GET    /api/users/                    # Listar usuarios
GET    /api/users/{id}/               # Obtener usuario por ID
PATCH  /api/users/{id}/               # Actualizar usuario
DELETE /api/users/{id}/               # Eliminar usuario
POST   /api/users/{id}/deactivate/   # Desactivar usuario
```

### Ejemplo: Crear usuario

```bash
curl -X POST http://localhost:8001/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "newuser",
    "password": "securepassword123"
  }'
```

Respuesta:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "username": "newuser",
  "is_active": true
}
```

## 🧪 Tests

```powershell
# Ejecutar todos los tests
pytest

# Solo tests de dominio (no requieren Django)
pytest users/tests/test_domain.py

# Solo tests de casos de uso (con mocks)
pytest users/tests/test_use_cases.py

# Tests de integración (con Django + BD)
pytest users/tests/test_integration.py -v

# Con cobertura
pytest --cov=users --cov-report=html
```

## 📨 Event-Driven Architecture

### Eventos Publicados

Este servicio publica los siguientes eventos a RabbitMQ:

| Evento | Routing Key | Descripción |
|--------|-------------|-------------|
| `UserCreated` | `user.created` | Se creó un nuevo usuario |
| `UserDeactivated` | `user.deactivated` | Se desactivó un usuario |
| `UserUpdated` | `user.updated` | Se actualizó la info de un usuario |

### Eventos Consumidos

Este servicio escucha eventos de otros servicios:

| Evento | Origen | Acción |
|--------|--------|--------|
| `TicketAssigned` | ticket-service | Notifica al usuario asignado |
| `TicketClosed` | ticket-service | Notifica al usuario sobre cierre |

### Iniciar Consumidor de Eventos

```powershell
# En terminal separado (con venv activado)
python -c "from users.messaging.consumer import RabbitMQConsumer; RabbitMQConsumer().start()"
```

## 🛠️ Tecnologías

- **Django 6.0+**: Framework web
- **Django REST Framework**: APIs REST
- **SQLite**: Base de datos (desarrollo)
- **PostgreSQL**: Base de datos (producción)
- **Pika**: Cliente RabbitMQ
- **Pytest**: Testing framework
- **CORS Headers**: Comunicación entre servicios

## 📝 Próximos Pasos

Para completar la implementación, seguir este orden:

1. ✅ **Estructura base creada** (COMPLETO)
2. ⏳ **Implementar entidades del dominio** (`domain/entities.py`)
3. ⏳ **Implementar eventos** (`domain/events.py`)
4. ⏳ **Implementar excepciones** (`domain/exceptions.py`)
5. ⏳ **Implementar factory** (`domain/factories.py`)
6. ⏳ **Implementar repositorio** (`infrastructure/repository.py`)
7. ⏳ **Implementar casos de uso** (`application/use_cases.py`)
8. ⏳ **Implementar ViewSets** (`views.py`)
9. ⏳ **Escribir tests**

Ver [ARCHITECTURE_DDD.md](./ARCHITECTURE_DDD.md) para guías detalladas de implementación.

## 🤝 Integración con Otros Servicios

### ticket-service
- Recibe eventos: `TicketAssigned`, `TicketClosed`
- Envía eventos: `UserDeactivated` (para validar asignaciones)

### assignment-service
- Recibe eventos: `UserCreated`, `UserDeactivated`
- Para gestionar asignaciones válidas

### notification-service
- Envía eventos: `UserNotified`
- Cuando se notifica exitosamente a un usuario

## 📚 Documentación

- [Arquitectura DDD completa](./ARCHITECTURE_DDD.md)
- [Guía de testing](./users/tests/__init__.py)
- [Configuración Django](./user_service/settings.py)

## 🐛 Debugging

### Admin de Django

Acceder a: `http://localhost:8001/admin/`

Permite ver/editar datos directamente en la BD.

### Verificar migraciones

```powershell
python manage.py showmigrations
```

### Crear nueva migración

```powershell
python manage.py makemigrations users
python manage.py migrate users
```

---

**Arquitectura:** DDD + Hexagonal + Event-Driven  
**Estado:** ✅ Estructura base completa | ⏳ Pendiente implementación de lógica  
**Mantenedor:** SistemaTickets Team
