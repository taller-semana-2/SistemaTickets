# Arquitectura DDD/EDA - Users Service

## 🎯 Resumen

Este microservicio ha sido diseñado desde cero aplicando **Domain-Driven Design (DDD)** y **Event-Driven Architecture (EDA)** siguiendo principios SOLID y arquitectura hexagonal (puertos y adaptadores).

## 📁 Estructura de Capas

```
users/
├── domain/                    # ❤️ CAPA DE DOMINIO (independiente del framework)
│   ├── entities.py           # Entidad User con reglas de negocio
│   ├── events.py             # Eventos de dominio (UserCreated, UserDeactivated, etc.)
│   ├── exceptions.py         # Excepciones de dominio
│   ├── factories.py          # UserFactory para creación válida
│   ├── repositories.py       # Interfaz UserRepository (Puerto)
│   └── event_publisher.py    # Interfaz EventPublisher (Puerto)
│
├── application/               # 🎼 CAPA DE APLICACIÓN (casos de uso)
│   └── use_cases.py          # CreateUserUseCase, DeactivateUserUseCase, etc.
│
├── infrastructure/            # 🔌 CAPA DE INFRAESTRUCTURA (adaptadores)
│   ├── repository.py         # DjangoUserRepository (Adaptador Django ORM)
│   └── event_publisher.py    # RabbitMQEventPublisher (Adaptador RabbitMQ)
│
├── messaging/                 # 📨 EVENT DRIVEN (consumidores de eventos)
│   ├── consumer.py           # Consumidor de eventos de RabbitMQ
│   └── handlers.py           # Handlers de eventos recibidos
│
├── tests/                     # 🧪 TESTING
│   ├── test_domain.py        # Tests unitarios de dominio
│   ├── test_use_cases.py     # Tests de casos de uso con mocks
│   └── test_integration.py   # Tests de integración con Django
│
├── views.py                   # 🌐 PRESENTACIÓN - ViewSets DRF (thin controllers)
├── serializers.py            # 📦 SERIALIZACIÓN - Input/Output de API
├── urls.py                    # 🛣️ ROUTING - URLs de la API
├── models.py                  # 💾 PERSISTENCIA - Modelos Django ORM
└── admin.py                   # 🔧 ADMIN - Interfaz de administración Django
```

## 🏗️ Principios Aplicados

### 1. **Separation of Concerns**
- **Dominio**: Reglas de negocio puras, sin dependencias externas
- **Aplicación**: Orquestación de operaciones de dominio
- **Infraestructura**: Implementaciones técnicas (Django, RabbitMQ)
- **Presentación**: Controladores HTTP (ViewSets)

### 2. **Dependency Inversion Principle (DIP)**
```
views → application → domain ← infrastructure
                        ^           |
                        |           |
                        └───────────┘
                      infraestructura implementa
                      interfaces del dominio
```

- Los casos de uso dependen de **abstracciones** (`UserRepository`, `EventPublisher`)
- Las implementaciones concretas dependen de las **interfaces**
- La dirección de dependencia apunta **hacia el dominio**

### 3. **Single Responsibility Principle (SRP)**
- `User Entity`: Reglas de negocio y validaciones
- `UserFactory`: Creación y validación de datos
- `Use Cases`: Orquestación de operaciones
- `Repository`: Abstracción de persistencia
- `ViewSet`: Traducción HTTP ↔ Dominio

## 📐 Reglas Arquitectónicas (CRÍTICAS)

### ✅ PERMITIDO

```python
# application/ puede importar de domain/
from users.domain.repositories import UserRepository
from users.domain.entities import User

# infrastructure/ puede importar de domain/ Y de frameworks
from users.domain.repositories import UserRepository
from django.db import models

# views.py puede importar de application/ e infrastructure/
from users.application.use_cases import CreateUserUseCase
from users.infrastructure.repository import DjangoUserRepository
```

### ❌ PROHIBIDO

```python
# domain/ NO puede importar de Django
from django.db import models  # ❌ NUNCA en domain/

# application/ NO puede importar de infrastructure/
from users.infrastructure.repository import DjangoUserRepository  # ❌

# domain/ NO puede importar de application/
from users.application.use_cases import CreateUserUseCase  # ❌
```

## 🔄 Flujo de Operaciones

### Crear Usuario

```
HTTP POST → ViewSet → CreateUserUseCase → UserFactory → User Entity
                                        ↓
                                 DjangoRepository → Django ORM
                                        ↓
                                 EventPublisher → RabbitMQ
```

**Código simplificado:**
```python
# 1. ViewSet recibe request HTTP
def create(request):
    serializer.is_valid()
    use_case.execute(email, username, password)

# 2. Use Case orquesta dominio
def execute(email, username, password):
    if repository.exists_by_email(email):
        raise UserAlreadyExists()
    
    user = UserFactory.create(email, username, password)
    saved_user = repository.save(user)
    
    event = UserCreated(...)
    event_publisher.publish(event, 'user.created')
    
    return saved_user

# 3. Factory crea entidad válida
def create(email, username, password):
    if '@' not in email:
        raise InvalidEmail()
    
    return User(id=uuid4(), email=email, ...)
```

### Evento de Otro Servicio

```
RabbitMQ → Consumer → Handler → Use Case → Domain
```

**Ejemplo:**
```python
# 1. Consumer recibe evento de ticket-service
# Evento: TicketAssigned(ticket_id, user_id)

# 2. Handler lo procesa
def handle(event_data):
    use_case.execute(user_id, ticket_id)

# 3. Use Case ejecuta lógica
def execute(user_id, ticket_id):
    user = repository.find_by_id(user_id)
    # Notificar al usuario sobre asignación
    # Publicar evento UserNotified
```

## 🧪 Testing Strategy

### Tests Unitarios (domain/)
```python
# NO necesitan Django ni base de datos
def test_user_deactivate():
    user = User('123', 'test@example.com', 'testuser', True)
    user.deactivate()
    assert user.is_active == False
```

### Tests de Casos de Uso (application/)
```python
# Usan mocks, NO tocan la base de datos
def test_create_user_use_case():
    mock_repo = Mock()
    mock_repo.exists_by_email.return_value = False
    
    use_case = CreateUserUseCase(mock_repo, mock_publisher)
    result = use_case.execute('test@example.com', 'user', 'pass')
    
    mock_repo.save.assert_called_once()
```

### Tests de Integración (tests/test_integration.py)
```python
# Usan Django ORM real y base de datos de test
@pytest.mark.django_db
def test_api_create_user():
    response = client.post('/api/users/', {...})
    assert response.status_code == 201
    assert UserModel.objects.filter(email='...').exists()
```

## 🚀 Comandos de Desarrollo

### Crear migraciones
```powershell
cd backend/users-service
.\venv\Scripts\Activate.ps1
python manage.py makemigrations
python manage.py migrate
```

### Ejecutar servidor de desarrollo
```powershell
python manage.py runserver 8001
```

### Ejecutar tests
```powershell
# Todos los tests
pytest

# Solo tests de dominio (rápidos)
pytest users/tests/test_domain.py

# Tests con cobertura
pytest --cov=users
```

### Iniciar consumidor de eventos (en terminal separado)
```powershell
python -c "from users.messaging.consumer import RabbitMQConsumer; RabbitMQConsumer().start()"
```

## 🔧 Próximos Pasos para Implementación

Ahora que tienes la estructura base, el orden de implementación es:

1. **Implementar entidades del dominio** (`domain/entities.py`)
   - Clase `User` con validaciones
   - Métodos como `deactivate()`, `change_email()`, etc.

2. **Definir eventos** (`domain/events.py`)
   - `UserCreated`, `UserDeactivated`, `UserUpdated`

3. **Crear excepciones** (`domain/exceptions.py`)
   - `UserAlreadyExists`, `InvalidEmail`, etc.

4. **Implementar factory** (`domain/factories.py`)
   - `UserFactory.create()` con validaciones

5. **Implementar repositorio** (`infrastructure/repository.py`)
   - `DjangoUserRepository` con ORM

6. **Implementar casos de uso** (`application/use_cases.py`)
   - `CreateUserUseCase`, `DeactivateUserUseCase`, etc.

7. **Implementar ViewSets** (`views.py`)
   - Conectar HTTP con casos de uso

8. **Implementar serializers** (`serializers.py`)
   - Input/Output de la API

9. **Tests**
   - Primero domain, luego use cases, luego integración

## 📚 Referencias

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)

## 💡 Beneficios de esta Arquitectura

✅ **Testeable**: Dominio sin dependencias = tests rápidos
✅ **Mantenible**: Separación clara de responsabilidades
✅ **Escalable**: Fácil agregar nuevos casos de uso
✅ **Flexible**: Cambiar tecnología sin tocar dominio
✅ **Event-Driven**: Comunicación asíncrona entre servicios
✅ **SOLID**: Principios aplicados en cada capa
