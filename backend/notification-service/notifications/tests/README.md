# Tests del Notification Service con DDD/EDA

Este directorio contiene los tests organizados por capas siguiendo la arquitectura limpia:

## Estructura

- `test_domain.py` - Tests de la capa de dominio (entidades, reglas de negocio)
- `test_use_cases.py` - Tests de casos de uso (application layer)
- `test_infrastructure.py` - Tests del repositorio Django (adaptadores)
- `test_views.py` - Tests del ViewSet (thin controllers)
- `test_integration.py` - Tests de integración (RabbitMQ, flujo completo)

## Ejecutar tests

```bash
# Todos los tests
python manage.py test notifications.tests

# Tests por archivo
python manage.py test notifications.tests.test_domain
python manage.py test notifications.tests.test_use_cases
python manage.py test notifications.tests.test_infrastructure
python manage.py test notifications.tests.test_views
python manage.py test notifications.tests.test_integration
```

## Cobertura

Los tests cubren:
- ✅ Reglas de negocio (marcar como leída, idempotencia)
- ✅ Eventos de dominio
- ✅ Casos de uso (orquestación)
- ✅ Repositorio (traducción dominio ↔ Django)
- ✅ ViewSet (delegación a casos de uso)
- ✅ Integración con RabbitMQ
