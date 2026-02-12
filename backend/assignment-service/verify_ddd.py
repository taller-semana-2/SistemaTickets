#!/usr/bin/env python
"""
Script de verificación de la arquitectura DDD.
Valida que todos los componentes estén correctamente estructurados.
"""
import os
import sys

def check_structure():
    """Verifica la estructura de carpetas"""
    print("🔍 Verificando estructura de carpetas...")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    assignments_path = os.path.join(base_path, 'assignments')
    
    required_paths = [
        'domain',
        'domain/entities.py',
        'domain/repository.py',
        'domain/events.py',
        'application',
        'application/use_cases',
        'application/use_cases/create_assignment.py',
        'application/use_cases/reassign_ticket.py',
        'application/event_publisher.py',
        'infrastructure',
        'infrastructure/django_models.py',
        'infrastructure/repository.py',
        'infrastructure/messaging',
        'infrastructure/messaging/event_publisher.py',
        'infrastructure/messaging/event_adapter.py',
    ]
    
    missing = []
    for path in required_paths:
        full_path = os.path.join(assignments_path, path)
        if not os.path.exists(full_path):
            missing.append(path)
    
    if missing:
        print("❌ Faltan archivos/carpetas:")
        for m in missing:
            print(f"   - {m}")
        return False
    else:
        print("✅ Estructura de carpetas correcta")
        return True


def check_imports():
    """Verifica que los imports funcionen"""
    print("\n🔍 Verificando imports...")
    
    try:
        # Dominio
        from assignments.domain.entities import Assignment
        from assignments.domain.repository import AssignmentRepository
        from assignments.domain.events import AssignmentCreated, AssignmentReassigned
        
        # Aplicación
        from assignments.application.event_publisher import EventPublisher
        from assignments.application.use_cases.create_assignment import CreateAssignment
        from assignments.application.use_cases.reassign_ticket import ReassignTicket
        
        # Infraestructura
        from assignments.infrastructure.django_models import TicketAssignmentModel
        from assignments.infrastructure.repository import DjangoAssignmentRepository
        from assignments.infrastructure.messaging.event_publisher import RabbitMQEventPublisher
        from assignments.infrastructure.messaging.event_adapter import TicketEventAdapter
        
        print("✅ Todos los imports funcionan correctamente")
        return True
        
    except ImportError as e:
        print(f"❌ Error en imports: {e}")
        return False


def check_domain_independence():
    """Verifica que el dominio no dependa de Django"""
    print("\n🔍 Verificando independencia del dominio...")
    
    domain_files = [
        'assignments/domain/entities.py',
        'assignments/domain/repository.py',
        'assignments/domain/events.py',
    ]
    
    forbidden_imports = ['django', 'rest_framework', 'pika', 'celery']
    
    issues = []
    for file_path in domain_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for forbidden in forbidden_imports:
                    if f'import {forbidden}' in content or f'from {forbidden}' in content:
                        issues.append(f"{file_path} importa {forbidden}")
    
    if issues:
        print("❌ El dominio tiene dependencias externas:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ El dominio es independiente")
        return True


def check_entity_validation():
    """Verifica que la entidad valide correctamente"""
    print("\n🔍 Verificando validaciones de la entidad...")
    
    try:
        from datetime import datetime
        from assignments.domain.entities import Assignment
        
        # Test 1: ticket_id vacío debe fallar
        try:
            Assignment(ticket_id="", priority="high", assigned_at=datetime.utcnow())
            print("❌ No validó ticket_id vacío")
            return False
        except ValueError:
            pass  # Esperado
        
        # Test 2: prioridad inválida debe fallar
        try:
            Assignment(ticket_id="TKT-001", priority="urgent", assigned_at=datetime.utcnow())
            print("❌ No validó prioridad inválida")
            return False
        except ValueError:
            pass  # Esperado
        
        # Test 3: datos válidos deben funcionar
        assignment = Assignment(
            ticket_id="TKT-001",
            priority="high",
            assigned_at=datetime.utcnow()
        )
        
        # Test 4: cambiar prioridad válida
        assignment.change_priority("low")
        assert assignment.priority == "low"
        
        # Test 5: cambiar prioridad inválida debe fallar
        try:
            assignment.change_priority("invalid")
            print("❌ No validó cambio de prioridad inválida")
            return False
        except ValueError:
            pass  # Esperado
        
        print("✅ Todas las validaciones funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en validaciones: {e}")
        return False


def main():
    """Ejecuta todas las verificaciones"""
    print("=" * 60)
    print("VERIFICACIÓN DE ARQUITECTURA DDD - ASSIGNMENT SERVICE")
    print("=" * 60)
    
    checks = [
        check_structure,
        check_imports,
        check_domain_independence,
        check_entity_validation,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Error en verificación: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("=" * 60)
        print("\n🎉 La refactorización DDD está completa y funcional")
        return 0
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
