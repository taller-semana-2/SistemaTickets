"""
CAPA DE INFRAESTRUCTURA - infrastructure/

📋 REGLA DE ORO: Esta capa contiene las IMPLEMENTACIONES de las interfaces del dominio.

✅ Puede contener:
- Implementaciones de repositorios (Django ORM, SQL)
- Implementaciones de event publisher (RabbitMQ, Kafka)
- Clientes HTTP externos
- Servicios de email, SMS, storage
- Mappers entre entidades de dominio y modelos de Django

✅ Puede depender de:
- domain/ (implementa sus interfaces)
- Django ORM, DRF, pika, celery, etc.

❌ NO puede contener:
- Lógica de negocio (debe estar en domain/)
- Casos de uso (deben estar en application/)

💡 La infraestructura es la capa ADAPTADORA entre el dominio puro y las tecnologías específicas.
   Permite cambiar de base de datos, mensajería, etc., sin tocar el dominio.
"""
