# Tests para la Arquitectura DDD/EDA

Esta carpeta contiene la suite completa de tests organizados por capas de la arquitectura.

## Estructura de Tests

```
tests/
├── __init__.py                  # Configuración de tests
├── test_domain.py              # Tests de dominio (reglas de negocio)
├── test_use_cases.py           # Tests de casos de uso
├── test_infrastructure.py      # Tests de adaptadores
├── test_views.py               # Tests de ViewSet (presentación)
└── test_integration.py         # Tests de integración end-to-end
```

## Capas y Responsabilidades

### 1. `test_domain.py` - Capa de Dominio

Tests de **lógica de negocio pura** (sin dependencias de Django):

- ✅ **TestTicketEntity**: Reglas de negocio de la entidad Ticket
  - Creación de tickets (siempre OPEN)
  - Cambios de estado (transiciones válidas)
  - Regla: No se puede modificar ticket CLOSED
  - Idempotencia de cambios de estado
  - Generación de eventos de dominio

- ✅ **TestTicketFactory**: Validación de creación
  - Validación de título y descripción
  - Eliminación de espacios en blanco
  - Rechazo de datos inválidos

- ✅ **TestDomainEvents**: Inmutabilidad de eventos
  - TicketCreated es frozen (inmutable)
  - TicketStatusChanged es frozen

**Características:**
- No requieren Django
- No requieren base de datos
- No requieren RabbitMQ
- Ejecución muy rápida
- Se pueden ejecutar con pytest puro

### 2. `test_use_cases.py` - Capa de Aplicación

Tests de **casos de uso con mocks**:

- ✅ **TestCreateTicketUseCase**: Crear tickets
  - Persistencia a través del repositorio
  - Publicación de eventos
  - Manejo de datos inválidos
  - Uso de factory para validación

- ✅ **TestChangeTicketStatusUseCase**: Cambiar estado
  - Aplicación de reglas de negocio
  - Publicación de eventos de cambio
  - Manejo de tickets cerrados
  - Manejo de tickets inexistentes
  - Idempotencia

**Características:**
- Usan mocks para Repository y EventPublisher
- No requieren Django ni BD
- Prueban orquestación de operaciones
- Verifican interacciones entre componentes

### 3. `test_infrastructure.py` - Capa de Infraestructura

Tests de **adaptadores con Django**:

- ✅ **TestDjangoTicketRepository**: Persistencia con Django ORM
  - Guardar nuevos tickets (asignación de ID)
  - Actualizar tickets existentes
  - Conversión Django ↔ Dominio
  - Consultas (find_by_id, find_all)
  - Eliminación

- ✅ **TestRabbitMQEventPublisher**: Publicación de eventos
  - Traducción de eventos a mensajes JSON
  - Declaración de exchange fanout
  - Publicación de mensajes
  - Manejo de errores de conexión

**Características:**
- Requieren Django y base de datos de test
- Usan mocks para RabbitMQ (no conexión real)
- Prueban implementaciones concretas
- Verifican integración con frameworks

### 4. `test_views.py` - Capa de Presentación

Tests de **ViewSet y HTTP**:

- ✅ **TestTicketViewSet**: Controladores HTTP
  - Ejecución de casos de uso desde views
  - Traducción HTTP ↔ Comandos
  - Manejo de excepciones de dominio
  - Validación de entrada HTTP

- ✅ **TestTicketSerializer**: Serialización DRF
  - Validación de campos
  - Rechazo de datos inválidos

- ✅ **TestTicketModel**: Modelo Django
  - Valores por defecto
  - Actualizaciones

**Características:**
- Prueban thin controllers (sin lógica de negocio)
- Verifican que ViewSet delega a casos de uso
- Comprueban traducción de errores HTTP

### 5. `test_integration.py` - Tests End-to-End

Tests de **flujos completos**:

- ✅ **TestTicketWorkflowIntegration**: Flujos de negocio
  - Crear y cambiar estado (flujo completo)
  - Regla: No modificar tickets cerrados
  - Idempotencia en cambios de estado

- ✅ **TestRabbitMQEventPublisherIntegration**: Integración con RabbitMQ
  - Publicación real a RabbitMQ (si está disponible)
  - Formato de mensajes
  - Manejo de exchange

- ✅ **TestRepositoryIntegration**: Integración con ORM
  - Conversión roundtrip Django ↔ Dominio
  - Actualizaciones concurrentes

**Características:**
- Usan componentes reales (BD, eventualmente RabbitMQ)
- Prueban flujos end-to-end
- Se saltan si RabbitMQ no está disponible
- Más lentos pero más exhaustivos

## Ejecutar Tests

### Todos los tests
```bash
cd backend/ticket-service
python manage.py test tickets.tests
```

### Por módulo específico
```bash
# Solo tests de dominio (rápidos)
python manage.py test tickets.tests.test_domain

# Solo tests de casos de uso
python manage.py test tickets.tests.test_use_cases

# Solo tests de infraestructura
python manage.py test tickets.tests.test_infrastructure

# Solo tests de views
python manage.py test tickets.tests.test_views

# Solo tests de integración
python manage.py test tickets.tests.test_integration
```

### Con pytest (alternativa)
```bash
# Instalar pytest y pytest-django
pip install pytest pytest-django

# Ejecutar todos los tests
pytest tickets/tests/

# Ejecutar un archivo específico
pytest tickets/tests/test_domain.py

# Ejecutar un test específico
pytest tickets/tests/test_domain.py::TestTicketEntity::test_create_ticket_with_valid_data

# Con verbose
pytest tickets/tests/ -v

# Con coverage
pytest tickets/tests/ --cov=tickets
```

## Pirámide de Tests

```
        /\
       /  \    Integration Tests (pocas, lentas, exhaustivas)
      /____\   
     /      \  
    / Views  \ Infrastructure Tests (medianas, usan Django)
   /__________\
  /            \
 /  Use Cases  \ Use Case Tests (muchas, rápidas, con mocks)
/________________\
     Domain       Domain Tests (muchas, muy rápidas, puras)
```

## Métricas de Cobertura

Objetivo de cobertura por capa:

- ✅ **Dominio**: 100% (crítico, reglas de negocio)
- ✅ **Casos de Uso**: 95%+ (orquestación)
- ✅ **Infraestructura**: 85%+ (adaptadores)
- ✅ **Views**: 80%+ (traducción HTTP)
- ✅ **Integración**: Flujos críticos

## Migración desde Tests Antiguos

### Tests Eliminados/Migrados

Los siguientes archivos antiguos han sido **deprecados**:

- ❌ `tickets/tests.py` → Actualizado con tests de compatibilidad
- ❌ `tickets/test_integration.py` → Deprecado, ver `tests/test_integration.py`
- ❌ `tickets/test_ddd.py` → Eliminado, funcionalidad en `tests/`

### Tests que Probaban Código Obsoleto

- ❌ Tests de `publish_ticket_created()` → Función eliminada
- ❌ Tests de acceso directo al ORM en views → Ya no aplica
- ❌ Tests del módulo `messaging/` → Módulo eliminado

### Nuevos Tests para Nueva Arquitectura

- ✅ Tests de entidades de dominio con reglas de negocio
- ✅ Tests de casos de uso con inyección de dependencias
- ✅ Tests de adaptadores (Repository, EventPublisher)
- ✅ Tests de ViewSet como thin controller

## Convenciones

### Naming
- Archivos: `test_*.py`
- Clases: `Test<ComponentName>`
- Métodos: `test_<what_it_does>`

### Estructura de Tests
```python
def test_descriptive_name(self):
    """Docstring explicando qué verifica el test."""
    # Arrange: Preparar datos y mocks
    # Act: Ejecutar la operación
    # Assert: Verificar resultados
```

### Mocks
- Mockear dependencias externas (Repository, EventPublisher)
- No mockear el objeto bajo prueba
- Verificar interacciones importantes (`assert_called_once`, etc.)

## Próximos Pasos

1. ✅ Agregar tests de edge cases
2. ✅ Medir cobertura con `coverage.py`
3. ✅ Agregar tests de performance
4. ✅ Configurar CI/CD para ejecutar tests automáticamente
5. ✅ Agregar mutation testing para verificar calidad de tests

## Referencias

- [ARCHITECTURE_DDD.md](../ARCHITECTURE_DDD.md) - Arquitectura general
- [COMPONENTS_TO_REMOVE.md](../COMPONENTS_TO_REMOVE.md) - Código obsoleto
- [QUICK_START_DDD.md](../QUICK_START_DDD.md) - Guía de desarrollo
