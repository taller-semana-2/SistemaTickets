# ✅ Checklist de Validación - Refactorización DDD

## 🎯 Validación Rápida (5 minutos)

### 1. Estructura de Archivos

```bash
# Verificar que existen las carpetas principales
ls -la assignments/domain/
ls -la assignments/application/
ls -la assignments/infrastructure/
```

**Debe contener:**
- ✅ `domain/entities.py`
- ✅ `domain/repository.py`
- ✅ `domain/events.py`
- ✅ `application/use_cases/create_assignment.py`
- ✅ `application/use_cases/reassign_ticket.py`
- ✅ `infrastructure/repository.py`
- ✅ `infrastructure/messaging/event_publisher.py`

### 2. Ejecutar Script de Verificación

```bash
python verify_ddd.py
```

**Output esperado:**
```
✅ Estructura de carpetas correcta
✅ Todos los imports funcionan correctamente
✅ El dominio es independiente
✅ Todas las validaciones funcionan correctamente
🎉 La refactorización DDD está completa y funcional
```

### 3. Verificar que Django Reconoce el Modelo

```bash
python manage.py showmigrations assignments
```

**Debe mostrar:**
```
assignments
 [X] 0001_initial
```

## 🔍 Validación Completa (15 minutos)

### 4. Test de Imports

```python
# En una shell de Python o Django shell
python manage.py shell

# Ejecutar:
from assignments.domain.entities import Assignment
from assignments.domain.repository import AssignmentRepository
from assignments.application.use_cases.create_assignment import CreateAssignment
from assignments.infrastructure.repository import DjangoAssignmentRepository

print("✅ Todos los imports funcionan")
```

### 5. Test de Validación de Dominio

```python
# En Django shell
from datetime import datetime
from assignments.domain.entities import Assignment

# Test 1: Validación de prioridad inválida
try:
    a = Assignment(ticket_id="TEST", priority="invalid", assigned_at=datetime.utcnow())
    print("❌ ERROR: No validó prioridad inválida")
except ValueError as e:
    print("✅ Validación de prioridad funciona:", str(e))

# Test 2: Validación de ticket_id vacío
try:
    a = Assignment(ticket_id="", priority="high", assigned_at=datetime.utcnow())
    print("❌ ERROR: No validó ticket_id vacío")
except ValueError as e:
    print("✅ Validación de ticket_id funciona:", str(e))

# Test 3: Creación válida
a = Assignment(ticket_id="TEST-001", priority="high", assigned_at=datetime.utcnow())
print("✅ Creación válida funciona:", a)
```

### 6. Test de Repositorio

```python
# En Django shell
from datetime import datetime
from assignments.infrastructure.repository import DjangoAssignmentRepository
from assignments.domain.entities import Assignment

repo = DjangoAssignmentRepository()

# Crear assignment
assignment = Assignment(
    ticket_id="TEST-REPO-001",
    priority="high",
    assigned_at=datetime.utcnow()
)

# Guardar
saved = repo.save(assignment)
print(f"✅ Assignment guardada con id: {saved.id}")

# Buscar por ticket_id
found = repo.find_by_ticket_id("TEST-REPO-001")
print(f"✅ Assignment encontrada: {found}")

# Buscar por id
found_by_id = repo.find_by_id(saved.id)
print(f"✅ Assignment encontrada por id: {found_by_id}")

# Limpiar
if saved.id:
    deleted = repo.delete(saved.id)
    print(f"✅ Assignment eliminada: {deleted}")
```

### 7. Test de Use Case

```python
# En Django shell
from assignments.infrastructure.repository import DjangoAssignmentRepository
from assignments.infrastructure.messaging.event_publisher import RabbitMQEventPublisher
from assignments.application.use_cases.create_assignment import CreateAssignment

repo = DjangoAssignmentRepository()

# Nota: RabbitMQEventPublisher necesita RabbitMQ corriendo
# Para test sin RabbitMQ, usar un mock:
class MockEventPublisher:
    def publish(self, event):
        print(f"📤 Mock: Evento publicado - {event.to_dict()['event_type']}")

event_publisher = MockEventPublisher()

# Ejecutar use case
use_case = CreateAssignment(repo, event_publisher)
result = use_case.execute(ticket_id="TEST-UC-001", priority="medium")

print(f"✅ Use Case ejecutado: {result}")

# Test de idempotencia
result2 = use_case.execute(ticket_id="TEST-UC-001", priority="medium")
print(f"✅ Idempotencia funciona (mismo id): {result.id == result2.id}")

# Limpiar
repo.delete(result.id)
```

### 8. Test de API REST

```bash
# Asegúrate de que el servidor está corriendo
python manage.py runserver

# En otra terminal:

# 1. Crear assignment
curl -X POST http://localhost:8000/assignments/ \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "TEST-API-001", "priority": "high"}'

# Debe retornar 201 Created con el objeto creado
# ✅ Verifica que se creó

# 2. Listar assignments
curl http://localhost:8000/assignments/

# Debe retornar lista incluyendo TEST-API-001
# ✅ Verifica que aparece

# 3. Reasignar
curl -X POST http://localhost:8000/assignments/reassign/ \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "TEST-API-001", "priority": "low"}'

# Debe retornar el objeto con priority="low"
# ✅ Verifica que cambió la prioridad

# 4. Verificar cambio
curl http://localhost:8000/assignments/ | grep TEST-API-001

# Debe mostrar priority: "low"
# ✅ Verifica que persistió el cambio
```

### 9. Test de Eventos (Opcional - Requiere RabbitMQ)

```bash
# Terminal 1: Iniciar consumidor
python messaging/consumer.py

# Terminal 2: Publicar evento de prueba
# (Desde el servicio de tickets o usando RabbitMQ management UI)

# Verificar logs del consumidor
# Debe mostrar:
# [ASSIGNMENT] Evento recibido y enviado a Celery: {...}
# [ASSIGNMENT] Ticket XXX asignado con prioridad YYY
```

## 📋 Checklist Final

### Código y Estructura
- [ ] `verify_ddd.py` pasa todas las verificaciones
- [ ] Estructura de carpetas domain/application/infrastructure existe
- [ ] Todos los archivos principales existen
- [ ] No hay errores de import

### Dominio
- [ ] Assignment entity valida ticket_id
- [ ] Assignment entity valida priority
- [ ] Eventos de dominio definidos (AssignmentCreated, AssignmentReassigned)
- [ ] Repository interface definida

### Aplicación
- [ ] CreateAssignment use case existe y funciona
- [ ] ReassignTicket use case existe y funciona
- [ ] EventPublisher interface definida
- [ ] Use cases emiten eventos

### Infraestructura
- [ ] DjangoAssignmentRepository implementado
- [ ] RabbitMQEventPublisher implementado
- [ ] TicketEventAdapter implementado
- [ ] Modelo Django compatible con migración existente

### API
- [ ] ViewSet refactorizado usa use cases
- [ ] GET /assignments/ funciona
- [ ] POST /assignments/ funciona
- [ ] POST /assignments/reassign/ funciona
- [ ] Serializers sin cambios
- [ ] URLs sin cambios

### Integración
- [ ] Django reconoce el modelo
- [ ] Migraciones funcionan
- [ ] Consumer de RabbitMQ funciona (si está configurado)
- [ ] Celery procesa tareas (si está configurado)
- [ ] Eventos se publican correctamente (si RabbitMQ está configurado)

### Documentación
- [ ] ARCHITECTURE_DDD.md creado
- [ ] BEFORE_AFTER.md creado
- [ ] MIGRATION_GUIDE.md creado
- [ ] REFACTORING_SUMMARY.md creado
- [ ] USAGE_GUIDE.md creado
- [ ] assignments/README.md creado
- [ ] INDEX.md creado
- [ ] DIAGRAM.md creado

### Tests
- [ ] Validaciones de entidad funcionan
- [ ] Repositorio funciona (save, find, delete)
- [ ] Use cases funcionan
- [ ] API REST funciona
- [ ] Idempotencia funciona

## 🚨 Problemas Comunes

### ❌ "No module named 'assignments.domain'"

**Solución:**
```bash
# Asegúrate de estar en el directorio correcto
cd backend/assignment-service

# Verifica PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.
```

### ❌ "Import pika could not be resolved"

**Causa:** Linter no encuentra pika (es normal si no está instalado localmente)

**Solución:** Ignorar si pika está en requirements.txt. El código funcionará en el contenedor.

### ❌ "ValueError: priority inválida"

**Causa:** Intentando usar prioridad no válida

**Solución:** Usar solo: `high`, `medium`, `low`

### ❌ "AssignmentRepository object is not callable"

**Causa:** Usando la interface en lugar de la implementación

**Solución:**
```python
# ❌ Incorrecto
from assignments.domain.repository import AssignmentRepository
repo = AssignmentRepository()  # Es una interface (ABC)

# ✅ Correcto
from assignments.infrastructure.repository import DjangoAssignmentRepository
repo = DjangoAssignmentRepository()  # Es la implementación
```

## ✅ Criterios de Éxito

La refactorización es exitosa si:

1. ✅ `verify_ddd.py` pasa todas las verificaciones
2. ✅ API REST funciona (GET, POST, reassign)
3. ✅ Validaciones de dominio funcionan
4. ✅ Repositorio funciona correctamente
5. ✅ Use cases ejecutan sin errores
6. ✅ No hay breaking changes en la API
7. ✅ Django migrations funcionan
8. ✅ Toda la documentación está completa

## 🎉 Validación Exitosa

Si todos los checks están marcados, la refactorización DDD está completa y lista para producción.

**Próximos pasos:**
1. Commit y push
2. Code review
3. Deployment a staging
4. Tests de integración
5. Deployment a producción

---

**Tiempo estimado de validación**: 15-20 minutos  
**Cobertura**: 100% de la funcionalidad refactorizada
