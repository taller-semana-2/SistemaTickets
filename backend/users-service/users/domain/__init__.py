"""
CAPA DE DOMINIO - Lógica de negocio pura, independiente del framework.

Esta capa contiene:
- Entidades: Objetos con identidad y reglas de negocio
- Eventos: Hechos importantes del dominio (inmutables)
- Excepciones: Violaciones de reglas de negocio
- Factories: Creación compleja de entidades
- Repositorios: Interfaces para persistencia (NO implementaciones)
- Event Publisher: Interfaz para publicar eventos (NO implementación)

REGLA DE ORO: Esta capa NO puede importar Django, DRF, Pika ni ningún framework.
"""
