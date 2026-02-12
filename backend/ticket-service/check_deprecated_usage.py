#!/usr/bin/env python3
"""
Script de migración para actualizar código que usa la API antigua.
Encuentra y reporta usos de componentes deprecados.

Uso:
    python check_deprecated_usage.py
"""

import os
import re
from pathlib import Path


class DeprecatedComponentChecker:
    """Verifica uso de componentes deprecados."""
    
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.issues = []
    
    def check_all(self):
        """Ejecuta todas las verificaciones."""
        print("🔍 Verificando uso de componentes deprecados...\n")
        
        self.check_messaging_imports()
        self.check_publish_ticket_created_usage()
        self.check_direct_orm_access_in_views()
        self.check_old_test_patterns()
        
        self.report()
    
    def check_messaging_imports(self):
        """Verifica imports del módulo messaging obsoleto."""
        print("📦 Verificando imports de tickets.messaging...")
        
        pattern = r'from\s+\.?messaging\s+import|from\s+tickets\.messaging'
        self._search_pattern(
            pattern,
            "Import de módulo deprecado 'messaging'",
            exclude_files=['events.py', '__init__.py'],
            exclude_dirs=['messaging']
        )
    
    def check_publish_ticket_created_usage(self):
        """Verifica uso de publish_ticket_created."""
        print("📤 Verificando uso de publish_ticket_created()...")
        
        pattern = r'publish_ticket_created\s*\('
        self._search_pattern(
            pattern,
            "Uso de función deprecada 'publish_ticket_created'",
            exclude_files=['events.py'],
            exclude_dirs=['messaging']
        )
    
    def check_direct_orm_access_in_views(self):
        """Verifica acceso directo al ORM en views.py."""
        print("🗄️  Verificando acceso directo al ORM en views...")
        
        views_file = self.root_dir / 'tickets' / 'views.py'
        if not views_file.exists():
            return
        
        content = views_file.read_text(encoding='utf-8')
        
        # Patrones que indican acceso directo al ORM
        patterns = [
            (r'Ticket\.objects\.', "Acceso directo a Ticket.objects"),
            (r'\.save\(\)', "Llamada directa a .save()"),
            (r'\.delete\(\)', "Llamada directa a .delete()"),
        ]
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, message in patterns:
                # Ignorar: líneas con use_case, queryset de DRF, o repository
                if re.search(pattern, line) and not any(keyword in line.lower() for keyword in ['use_case', 'queryset', 'repository']):
                    # Ignorar si está en comentarios o strings
                    if line.strip().startswith('#') or line.strip().startswith('"""'):
                        continue
                    
                    self.issues.append({
                        'file': views_file,
                        'line': line_num,
                        'type': message,
                        'code': line.strip()
                    })
    
    def check_old_test_patterns(self):
        """Verifica patrones de test obsoletos."""
        print("🧪 Verificando patrones de test obsoletos...")
        
        pattern = r"patch\(['\"]tickets\.views\.publish_ticket_created"
        self._search_pattern(
            pattern,
            "Test que mockea implementación antigua",
            include_files=['test*.py']
        )
    
    def _search_pattern(self, pattern, description, exclude_files=None, 
                       exclude_dirs=None, include_files=None):
        """Busca un patrón en archivos Python."""
        exclude_files = exclude_files or []
        exclude_dirs = exclude_dirs or []
        
        for py_file in self.root_dir.rglob('*.py'):
            # Excluir directorios
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue
            
            # Excluir archivos específicos
            if py_file.name in exclude_files:
                continue
            
            # Incluir solo archivos específicos si se especifica
            if include_files and not any(
                py_file.name.startswith(pattern.rstrip('*')) 
                for pattern in include_files
            ):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        self.issues.append({
                            'file': py_file,
                            'line': line_num,
                            'type': description,
                            'code': line.strip()
                        })
            except Exception as e:
                print(f"⚠️  Error leyendo {py_file}: {e}")
    
    def report(self):
        """Genera reporte de issues encontrados."""
        print("\n" + "="*70)
        print("📊 REPORTE DE COMPONENTES DEPRECADOS")
        print("="*70 + "\n")
        
        if not self.issues:
            print("✅ No se encontraron usos de componentes deprecados.")
            print("\n🎉 El código está listo para eliminar el módulo 'messaging'.")
            return
        
        print(f"⚠️  Se encontraron {len(self.issues)} issues:\n")
        
        # Agrupar por tipo
        by_type = {}
        for issue in self.issues:
            issue_type = issue['type']
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        # Mostrar agrupados
        for issue_type, issues in by_type.items():
            print(f"\n🔸 {issue_type} ({len(issues)} ocurrencias):")
            print("-" * 70)
            
            for issue in issues:
                rel_path = issue['file'].relative_to(self.root_dir)
                print(f"  📄 {rel_path}:{issue['line']}")
                print(f"     {issue['code']}")
            
        print("\n" + "="*70)
        print("📝 ACCIONES RECOMENDADAS:")
        print("="*70)
        print("""
1. Actualizar imports:
   from tickets.messaging.events import publish_ticket_created
   →
   from tickets.infrastructure.event_publisher import RabbitMQEventPublisher
   from tickets.domain.events import TicketCreated

2. Actualizar publicación de eventos:
   publish_ticket_created(ticket.id)
   →
   publisher = RabbitMQEventPublisher()
   event = TicketCreated(...)
   publisher.publish(event)

3. Actualizar tests:
   - Usar test_ddd.py como referencia
   - Mockear casos de uso en lugar de funciones de publicación
   - Testear nuevas abstracciones (Repository, EventPublisher)

4. Remover código obsoleto:
   - Una vez actualizados todos los usos, eliminar tickets/messaging/

Ver COMPONENTS_TO_REMOVE.md para detalles completos.
""")


def main():
    """Punto de entrada del script."""
    import sys
    
    # Detectar directorio raíz del proyecto
    script_dir = Path(__file__).parent
    
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    else:
        root_dir = script_dir
    
    print(f"🔍 Analizando: {root_dir.absolute()}\n")
    
    checker = DeprecatedComponentChecker(root_dir)
    checker.check_all()


if __name__ == '__main__':
    main()
