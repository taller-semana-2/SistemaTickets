# Guía de Migración - Assignment Service DDD

## ⚠️ Pre-Migración

### Backup de Sistema

```bash
# 1. Backup de base de datos
docker exec assignment-db pg_dump -U assessment_user assessment_db > backup_assignment.sql

# 2. Backup de código (si no está en git)
cp -r assignment-service assignment-service.backup

# 3. Verificar que RabbitMQ y Celery están detenidos
docker-compose stop rabbitmq
docker-compose stop celery
```

## 🚀 Proceso de Migración

### Opción A: Sistema Nuevo (Recomendado para desarrollo)

Si estás instalando el servicio por primera vez:

```bash
# 1. Clonar/Copiar el código refactorizado
cd backend/assignment-service

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 5. Aplicar migraciones
python manage.py migrate

# 6. Verificar arquitectura
python verify_ddd.py

# 7. Iniciar servicios
python manage.py runserver  # Terminal 1
celery -A assessment_service worker -l info  # Terminal 2
python messaging/consumer.py  # Terminal 3
```

### Opción B: Actualización en Sistema Existente

Si ya tienes el servicio funcionando:

```bash
# 1. Detener servicios
docker-compose stop assignment-service celery-assignment rabbitmq-consumer

# 2. Actualizar código
# (Los archivos ya están refactorizados en tu workspace)

# 3. No requiere nuevas migraciones
# El modelo es compatible con la migración existente

# 4. Verificar arquitectura
docker-compose exec assignment-service python verify_ddd.py

# 5. Reiniciar servicios
docker-compose up -d assignment-service celery-assignment rabbitmq-consumer

# 6. Verificar logs
docker-compose logs -f assignment-service
```

## ✅ Verificación Post-Migración

### 1. Verificar Arquitectura

```bash
python verify_ddd.py
```

**Output esperado:**
```
============================================================
VERIFICACIÓN DE ARQUITECTURA DDD - ASSIGNMENT SERVICE
============================================================
🔍 Verificando estructura de carpetas...
✅ Estructura de carpetas correcta

🔍 Verificando imports...
✅ Todos los imports funcionan correctamente

🔍 Verificando independencia del dominio...
✅ El dominio es independiente

🔍 Verificando validaciones de la entidad...
✅ Todas las validaciones funcionan correctamente

============================================================
✅ TODAS LAS VERIFICACIONES PASARON
============================================================

🎉 La refactorización DDD está completa y funcional
```

### 2. Verificar Base de Datos

```bash
# Conectar a base de datos
docker exec -it assignment-db psql -U assessment_user -d assessment_db

# Verificar tabla
\dt assignments_ticketassignment

# Listar registros
SELECT * FROM assignments_ticketassignment LIMIT 5;

# Salir
\q
```

### 3. Verificar API

```bash
# Health check
curl http://localhost:8000/assignments/

# Crear asignación de prueba
curl -X POST http://localhost:8000/assignments/ \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TEST-001",
    "priority": "high"
  }'

# Verificar que se creó
curl http://localhost:8000/assignments/ | grep TEST-001

# Limpiar prueba (opcional)
# DELETE /assignments/{id}/
```

### 4. Verificar Eventos

```bash
# Terminal 1: Ver logs del consumer
docker-compose logs -f rabbitmq-consumer

# Terminal 2: Publicar evento de prueba (desde ticket-service)
# O usar RabbitMQ management UI: http://localhost:15672
```

### 5. Verificar Celery

```bash
# Ver logs de Celery
docker-compose logs -f celery-assignment

# Deberías ver:
# [ASSIGNMENT] Esperando eventos...
# [ASSIGNMENT] Evento recibido y enviado a Celery: {...}
```

## 🔄 Rollback

Si algo falla y necesitas volver atrás:

```bash
# 1. Detener servicios
docker-compose stop assignment-service

# 2. Restaurar código anterior
cp -r assignment-service.backup/* assignment-service/

# 3. Restaurar base de datos (si es necesario)
docker exec -i assignment-db psql -U assessment_user -d assessment_db < backup_assignment.sql

# 4. Reiniciar servicios
docker-compose up -d assignment-service
```

## 🧪 Tests de Validación

### Test Manual Completo

```bash
# 1. Crear asignación vía API
curl -X POST http://localhost:8000/assignments/ \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "MIGRATION-TEST-001", "priority": "high"}'

# 2. Listar asignaciones
curl http://localhost:8000/assignments/ | jq '.[] | select(.ticket_id=="MIGRATION-TEST-001")'

# 3. Reasignar ticket
curl -X POST http://localhost:8000/assignments/reassign/ \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "MIGRATION-TEST-001", "priority": "low"}'

# 4. Verificar cambio
curl http://localhost:8000/assignments/ | jq '.[] | select(.ticket_id=="MIGRATION-TEST-001")'

# 5. Verificar en base de datos
docker exec -it assignment-db psql -U assessment_user -d assessment_db \
  -c "SELECT * FROM assignments_ticketassignment WHERE ticket_id='MIGRATION-TEST-001';"

# 6. Limpiar
# Borrar manualmente o por API
```

### Test Automatizado

```bash
# Ejecutar tests de Django
python manage.py test assignments

# O con pytest
pytest assignments/
```

## 📊 Checklist de Migración

- [ ] Backup de base de datos creado
- [ ] Backup de código creado
- [ ] Servicios detenidos
- [ ] Código actualizado
- [ ] Dependencias instaladas
- [ ] Variables de entorno configuradas
- [ ] Migraciones aplicadas (si es nuevo)
- [ ] `verify_ddd.py` ejecutado exitosamente
- [ ] Servicios reiniciados
- [ ] API funcionando (GET /assignments/)
- [ ] Creación de asignaciones funcionando
- [ ] Reasignación funcionando
- [ ] Consumer de RabbitMQ funcionando
- [ ] Celery worker funcionando
- [ ] Eventos se publican correctamente
- [ ] Tests pasan
- [ ] Logs sin errores

## 🚨 Problemas Comunes

### Error: "No module named 'assignments.domain'"

**Causa**: Python no encuentra el módulo.  
**Solución**:
```bash
# Verificar que estás en el directorio correcto
pwd  # Debe ser assignment-service/

# Verificar PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.

# O reinstalar en modo desarrollo
pip install -e .
```

### Error: "django.db.utils.OperationalError: FATAL: database does not exist"

**Causa**: Base de datos no existe.  
**Solución**:
```bash
# Crear base de datos
docker exec -it assignment-db psql -U postgres \
  -c "CREATE DATABASE assessment_db OWNER assessment_user;"

# Aplicar migraciones
python manage.py migrate
```

### Error: "pika.exceptions.AMQPConnectionError"

**Causa**: RabbitMQ no disponible.  
**Solución**:
```bash
# Verificar que RabbitMQ está corriendo
docker-compose ps rabbitmq

# Si no está corriendo, iniciarlo
docker-compose up -d rabbitmq

# Verificar logs
docker-compose logs rabbitmq
```

### Error: "AssignmentRepository object has no attribute 'save'"

**Causa**: No se está usando la implementación correcta.  
**Solución**:
```python
# Asegúrate de usar DjangoAssignmentRepository
from assignments.infrastructure.repository import DjangoAssignmentRepository

repository = DjangoAssignmentRepository()  # ✅ Correcto
# No: repository = AssignmentRepository()  # ❌ Incorrecto (es una interface)
```

## 📞 Soporte

Si encuentras problemas durante la migración:

1. Revisar logs: `docker-compose logs -f assignment-service`
2. Ejecutar: `python verify_ddd.py`
3. Consultar: `ARCHITECTURE_DDD.md` y `USAGE_GUIDE.md`
4. Verificar configuración: `assessment_service/settings.py`

## 🎯 Siguientes Pasos Post-Migración

1. **Tests**: Implementar tests unitarios y de integración
2. **Monitoring**: Agregar métricas y alertas
3. **Documentation**: Documentar reglas de negocio específicas
4. **Performance**: Optimizar queries y cache si es necesario
5. **Security**: Revisar permisos y autenticación

---

**Tiempo estimado de migración**: 15-30 minutos  
**Downtime requerido**: 5-10 minutos (solo durante restart de servicios)  
**Nivel de riesgo**: Bajo (100% compatible con sistema anterior)
