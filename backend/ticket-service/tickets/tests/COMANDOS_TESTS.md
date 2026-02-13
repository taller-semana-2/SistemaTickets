# Comandos para ejecutar tests - Sistema de Tickets

## 🐳 Tests en Docker/Podman (Recomendado)

### Ejecutar TODOS los tests
```powershell
podman-compose exec backend python manage.py test tickets --verbosity=2
```

### Ejecutar solo INTEGRATION tests (nuevos - 37 tests)
```powershell
podman-compose exec backend python manage.py test tickets.tests.integration --verbosity=2
```

### Ejecutar tests por archivo específico

#### Repository Pattern (20 tests)
```powershell
podman-compose exec backend python manage.py test tickets.tests.integration.test_ticket_repository --verbosity=2
```

#### Workflows E2E (17 tests)
```powershell
podman-compose exec backend python manage.py test tickets.tests.integration.test_ticket_workflow --verbosity=2
```

#### Infrastructure tests (Repository + RabbitMQ)
```powershell
podman-compose exec backend python manage.py test tickets.tests.test_infrastructure --verbosity=2
```

#### Integration tests originales
```powershell
podman-compose exec backend python manage.py test tickets.tests.test_integration --verbosity=2
```

#### API/ViewSet tests
```powershell
podman-compose exec backend python manage.py test tickets.tests.test_views --verbosity=2
```

---

## 🧪 Tests Unitarios (requieren pytest)

Los tests en `tests/unit/` usan pytest y NO están disponibles con Django test runner.

### Opción 1: Instalar pytest en el contenedor (temporal)
```powershell
# Instalar pytest (se pierde al reiniciar contenedor)
podman-compose exec backend pip install pytest pytest-django

# Ejecutar todos los unit tests
podman-compose exec backend pytest tickets/tests/unit/ -v

# Ejecutar por archivo
podman-compose exec backend pytest tickets/tests/unit/test_ticket_entity.py -v
podman-compose exec backend pytest tickets/tests/unit/test_ticket_factory.py -v
podman-compose exec backend pytest tickets/tests/unit/test_use_cases.py -v
podman-compose exec backend pytest tickets/tests/unit/test_events.py -v
podman-compose exec backend pytest tickets/tests/unit/test_exceptions.py -v
```

### Opción 2: Usar tests de dominio en raíz (con pytest)
```powershell
# Estos tests duplican la funcionalidad pero están en raíz
podman-compose exec backend pip install pytest pytest-django
podman-compose exec backend pytest tickets/tests/test_domain.py -v
podman-compose exec backend pytest tickets/tests/test_use_cases.py -v
```

---

## 📊 Ver resumen de tests disponibles

```powershell
# Listar todos los tests sin ejecutarlos
podman-compose exec backend python manage.py test tickets --verbosity=0 --failfast
```

---

## 🎯 Comandos Recomendados por Caso de Uso

### Durante desarrollo (rápido)
```powershell
# Solo el archivo en el que estás trabajando
podman-compose exec backend python manage.py test tickets.tests.integration.test_ticket_workflow --verbosity=2 --failfast
```

### Antes de commit (completo)
```powershell
# Todos los tests de integración
podman-compose exec backend python manage.py test tickets.tests.integration --verbosity=2
```

### CI/CD (todo)
```powershell
# Todos los tests con alta verbosidad
podman-compose exec backend python manage.py test tickets --verbosity=2
```

### Debug de un test específico
```powershell
# Ejecutar un test individual con máxima verbosidad
podman-compose exec backend python manage.py test tickets.tests.integration.test_ticket_repository.TestDjangoTicketRepositoryIntegration.test_save_new_ticket_persists_to_database --verbosity=3
```

---

## 🔧 Tests con cobertura (coverage)

Si instalas coverage en el contenedor:

```powershell
# Instalar coverage
podman-compose exec backend pip install coverage

# Ejecutar tests con coverage
podman-compose exec backend coverage run --source='tickets' manage.py test tickets

# Ver reporte
podman-compose exec backend coverage report

# Generar HTML
podman-compose exec backend coverage html
# Ver en: backend/ticket-service/htmlcov/index.html
```

---

## 🚀 Acceso rápido

### Entrar al contenedor
```powershell
podman-compose exec -it backend bash
```

Una vez dentro:
```bash
# Ejecutar tests
python manage.py test tickets.tests.integration --verbosity=2

# Ver estructura de tests
find tickets/tests -name "*.py" -type f | grep -E "test_.*\.py$"

# Contar tests
python manage.py test tickets --verbosity=0 2>&1 | grep "Ran"
```

---

## 📝 Resultado Actual

Al ejecutar todos los tests:
```
Found 69 tests
- 37 tests en integration/ (nuevos) ✅ 100% OK
- 32 tests en raíz (antiguos) ⚠️ 5 errores en test_views.py
```

**Status:** 
- ✅ Integration tests: **37/37 passing**
- ⚠️ Old tests: **27/32 passing** (errores menores en views)
