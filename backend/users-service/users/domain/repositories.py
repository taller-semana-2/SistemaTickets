"""
domain/repositories.py

🎯 PROPÓSITO:
Define las INTERFACES de los repositorios (patrones Abstract Repository).

⚠️ IMPORTANTE: Este archivo contiene SOLO interfaces (clases abstractas con ABC).
Las IMPLEMENTACIONES van en infrastructure/repository.py

📐 ESTRUCTURA:
- Interfaces que definen el contrato para persistir/recuperar entidades
- Métodos abstractos que deben ser implementados
- NO contiene lógica de persistencia real
- Permite inyección de dependencias

✅ EJEMPLO de lo que DEBE ir aquí:
    from abc import ABC, abstractmethod
    from typing import Optional, List
    from .entities import User
    
    class UserRepository(ABC):
        '''Contrato para persistir y recuperar usuarios del dominio'''
        
        @abstractmethod
        def save(self, user: User) -> User:
            '''Persiste un usuario. Devuelve el usuario guardado'''
            pass
        
        @abstractmethod
        def find_by_id(self, user_id: str) -> Optional[User]:
            '''Busca un usuario por su ID. Devuelve None si no existe'''
            pass
        
        @abstractmethod
        def find_by_email(self, email: str) -> Optional[User]:
            '''Busca un usuario por su email. Devuelve None si no existe'''
            pass
        
        @abstractmethod
        def find_all(self) -> List[User]:
            '''Devuelve todos los usuarios'''
            pass
        
        @abstractmethod
        def exists_by_email(self, email: str) -> bool:
            '''Verifica si existe un usuario con ese email'''
            pass

❌ NO debe:
- Implementar los métodos (solo abstractos)
- Importar Django ORM
- Contener consultas SQL o ORM

💡 Al depender de interfaces, el dominio no se acopla a la tecnología de persistencia.
"""
