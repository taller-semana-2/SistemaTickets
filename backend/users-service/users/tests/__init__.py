"""
CAPA DE TESTING - tests/

📋 PROPÓSITO: Tests organizados por capa para garantizar calidad y cobertura.

tipos de tests:
1️⃣ test_domain.py
   - Tests unitarios de entidades
   - Tests de factories
   - Tests de validaciones
   - NO necesitan Django ni base de datos

2️⃣ test_use_cases.py
   - Tests de casos de uso con mocks
   - Verifican la orquestación correcta
   - Usan repositorios mockeados

3️⃣ test_integration.py
   - Tests de integración con Django ORM
   - Tests de API endpoints
   - Usan base de datos de test

💡 Estructura de tests clara = código mantenible y confiable.
"""
