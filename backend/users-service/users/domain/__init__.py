"""
CAPA DE DOMINIO - domain/

📋 REGLA DE ORO: Esta capa NO puede depender de Django ni de ningún framework externo.

✅ Puede contener:
- Entidades del dominio (clases con lógica de negocio)
- Value Objects (objetos inmutables)
- Eventos de dominio
- Excepciones de dominio
- Interfaces de repositorios (SOLO interfaces, NO implementaciones)
- Factories para crear entidades válidas

❌ NO puede contener:
- Imports de Django (models, ORM, views, etc.)
- Imports de DRF (serializers, viewsets, etc.)
- Imports de pika, celery, etc.
- Lógica de persistencia
- Lógica de infraestructura

💡 El dominio es el CORAZÓN de la aplicación. Debe ser PURO y testeable sin dependencias.
"""
