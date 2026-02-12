"""
CAPA DE APLICACIÓN - application/

📋 REGLA DE ORO: Esta capa orquesta la lógica del dominio para ejecutar casos de uso.

✅ Puede contener:
- Casos de uso (Use Cases) = flujos de negocio específicos
- Comandos y consultas (CQRS pattern)
- Validaciones de entrada (input validation)
- Orquestación de múltiples operaciones de dominio
- Transacciones

✅ Puede depender de:
- domain/ (entidades, factories, interfaces de repositorios)

❌ NO puede contener:
- Lógica de negocio (debe estar en domain/)
- Imports de Django ORM (models.py)
- Detalles de implementación de persistencia
- Lógica de presentación (HTTP, serialización)

❌ NO puede depender de:
- infrastructure/ (solo de las interfaces del dominio)
- views.py, serializers.py

💡 Los Use Cases son los "entry points" de la lógica de negocio.
   Reciben datos primitivos, coordinan el dominio, devuelven resultados.
"""
