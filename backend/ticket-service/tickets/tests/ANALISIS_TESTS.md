# Análisis de Tests - Sistema de Tickets

## Estructura Actual

### 📁 Tests en raíz `tests/`

| Archivo | Tipo | Líneas | Contenido | Estado |
|---------|------|--------|-----------|--------|
| **test_domain.py** | pytest | 238 | Entidad Ticket, Factory, Eventos | ⚠️ DUPLICADO |
| **test_use_cases.py** | pytest | 266 | CreateTicket, ChangeStatus con mocks | ⚠️ DUPLICADO |
| **test_infrastructure.py** | Django | 244 | Repository Django, RabbitMQ Publisher | ✅ MANTENER |
| **test_integration.py** | Django | 264 | Workflows, RabbitMQ, Repository | ✅ MANTENER |
| **test_views.py** | Django | 230 | ViewSet, Serializer, API endpoints | ✅ MANTENER |

### 📁 Tests nuevos `tests/unit/`

| Archivo | Tests | Contenido |
|---------|-------|-----------|
| test_ticket_entity.py | 33 | Entidad Ticket + State Machine |
| test_ticket_factory.py | 15 | Validación Factory |
| test_use_cases.py | 13 | Casos de uso con mocks |
| test_events.py | 13 | Eventos de dominio |
| test_exceptions.py | 15 | Excepciones |

### 📁 Tests nuevos `tests/integration/`

| Archivo | Tests | Contenido |
|---------|-------|-----------|
| test_ticket_repository.py | 20 | Repository pattern con BD real |
| test_ticket_workflow.py | 17 | Workflows completos end-to-end |

---

## 🎯 Recomendaciones

### ❌ ELIMINAR (Duplicados)

1. **test_domain.py** - Ya cubierto por:
   - `unit/test_ticket_entity.py`
   - `unit/test_ticket_factory.py`
   - `unit/test_events.py`

2. **test_use_cases.py** - Ya cubierto por:
   - `unit/test_use_cases.py`

### ✅ MANTENER (Valor único)

1. **test_infrastructure.py** - Tests específicos de:
   - DjangoTicketRepository (con mocks)
   - RabbitMQEventPublisher (con mocks de pika)
   - Útil para tests de infraestructura aislados

2. **test_integration.py** - Tests de:
   - Workflow completo con casos de uso
   - RabbitMQ integration tests
   - Repository integration tests
   - **Nota:** Tiene overlap con `integration/test_ticket_workflow.py` pero cubre diferentes escenarios

3. **test_views.py** - ESENCIAL:
   - Tests del ViewSet (API REST)
   - Serializers
   - Validación HTTP
   - **NO hay equivalente en la nueva estructura**

---

## 📋 Cobertura Final

Con la eliminación de duplicados tendríamos:

**Unit Tests (dominio puro):**
- ✅ Entidades y reglas de negocio
- ✅ Factory y validaciones
- ✅ Eventos de dominio
- ✅ Excepciones
- ✅ Casos de uso (mocked)

**Integration Tests (con BD/infraestructura):**
- ✅ Repository pattern
- ✅ Workflows E2E
- ✅ Event publishing
- ✅ Infrastructure adapters

**API Tests:**
- ✅ ViewSet endpoints
- ✅ Serializers
- ✅ HTTP validation

---

## 🚀 Comandos de Ejecución

### Dentro del contenedor Docker:

```bash
# Todos los tests (Django test runner)
podman-compose exec backend python manage.py test tickets

# Solo tests de integración (nuevos)
podman-compose exec backend python manage.py test tickets.tests.integration

# Solo infrastructure + views + integration (antiguos)
podman-compose exec backend python manage.py test tickets.tests.test_infrastructure tickets.tests.test_integration tickets.tests.test_views

# Tests individuales
podman-compose exec backend python manage.py test tickets.tests.integration.test_ticket_repository
podman-compose exec backend python manage.py test tickets.tests.integration.test_ticket_workflow
podman-compose exec backend python manage.py test tickets.tests.test_views
```

### Tests Unitarios (requieren pytest - no instalado):

Los tests en `unit/` están diseñados para pytest pero el contenedor no lo tiene instalado.

**Opción 1:** Ejecutarlos con pytest (requiere instalación):
```bash
# Si instalas pytest
podman-compose exec backend pip install pytest
podman-compose exec backend pytest tickets/tests/unit/ -v
```

**Opción 2:** Los tests en raíz (test_domain.py, test_use_cases.py) cubren lo mismo y usan pytest también, así que si quieres tests unitarios de dominio, **mantén esos en lugar de eliminarlos**.

---

## 💡 Decisión Recomendada

**Opción A - Mantener ambos (máxima cobertura):**
- Mantener test_domain.py y test_use_cases.py en raíz (pytest)
- Mantener unit/ (mejores tests pero requieren pytest)
- Resultado: Redundancia pero flexibilidad

**Opción B - Consolidar (recomendado):**
- ✅ ELIMINAR: test_domain.py, test_use_cases.py
- ✅ MANTENER: test_infrastructure.py, test_integration.py, test_views.py
- ✅ MANTENER: Toda la estructura unit/ e integration/
- Resultado: Estructura limpia, sin duplicados

**Opción C - Solo Django tests:**
- ✅ ELIMINAR: Carpeta unit/ completa
- ✅ MANTENER: test_domain.py, test_use_cases.py, test_infrastructure.py, test_integration.py, test_views.py
- Resultado: Todo ejecutable con Django test runner (sin necesidad de pytest)
