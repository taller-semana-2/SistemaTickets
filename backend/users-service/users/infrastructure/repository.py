"""
Django Repository - Implementación del repositorio usando Django ORM.
Adaptador que traduce entre el dominio y la persistencia.
"""

from typing import Optional, List

from ..domain.entities import User as DomainUser
from ..domain.repositories import UserRepository
from ..models import User as DjangoUser


class DjangoUserRepository(UserRepository):
    """
    Implementación del repositorio usando Django ORM.
    Traduce entre entidades de dominio y modelos de Django.
    """
    
    def save(self, user: DomainUser) -> DomainUser:
        """
        Persiste un usuario en la base de datos (crear o actualizar).
        
        Args:
            user: Entidad de dominio
            
        Returns:
            La entidad con el ID asignado
        """
        if user.id:
            # Actualizar usuario existente
            django_user = DjangoUser.objects.get(pk=user.id)
            django_user.email = user.email
            django_user.username = user.username
            django_user.password_hash = user.password_hash
            django_user.is_active = user.is_active
            django_user.save(update_fields=['email', 'username', 'password_hash', 'is_active'])
        else:
            # Crear nuevo usuario
            django_user = DjangoUser.objects.create(
                email=user.email,
                username=user.username,
                password_hash=user.password_hash,
                is_active=user.is_active
            )
            user.id = str(django_user.id)
        
        return user
    
    def find_by_id(self, user_id: str) -> Optional[DomainUser]:
        """
        Busca un usuario por ID y lo convierte a entidad de dominio.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Entidad de dominio o None si no existe
        """
        try:
            django_user = DjangoUser.objects.get(pk=user_id)
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None
    
    def find_by_email(self, email: str) -> Optional[DomainUser]:
        """
        Busca un usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Entidad de dominio o None si no existe
        """
        try:
            django_user = DjangoUser.objects.get(email=email.lower())
            return self._to_domain(django_user)
        except DjangoUser.DoesNotExist:
            return None
    
    def find_all(self) -> List[DomainUser]:
        """
        Obtiene todos los usuarios ordenados por fecha de creación.
        
        Returns:
            Lista de entidades de dominio
        """
        django_users = DjangoUser.objects.all().order_by('-created_at')
        return [self._to_domain(du) for du in django_users]
    
    def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email: Email a verificar
            
        Returns:
            True si existe
        """
        return DjangoUser.objects.filter(email=email.lower()).exists()
    
    def delete(self, user_id: str) -> None:
        """
        Elimina un usuario por ID.
        
        Args:
            user_id: ID del usuario a eliminar
        """
        DjangoUser.objects.filter(pk=user_id).delete()
    
    def to_django_model(self, domain_user: DomainUser) -> DjangoUser:
        """
        Convierte una entidad de dominio a modelo Django sin hacer query adicional.
        Útil para serialización en la capa de presentación.
        
        Args:
            domain_user: Entidad de dominio
            
        Returns:
            Modelo Django (puede no estar guardado en BD)
        """
        if domain_user.id:
            # Si tiene ID, buscar el modelo existente para mantener metadata de Django
            try:
                django_user = DjangoUser.objects.get(pk=domain_user.id)
                # Actualizar valores desde la entidad de dominio
                django_user.email = domain_user.email
                django_user.username = domain_user.username
                django_user.password_hash = domain_user.password_hash
                django_user.is_active = domain_user.is_active
                return django_user
            except DjangoUser.DoesNotExist:
                pass
        
        # Crear instancia Django en memoria (no guardada)
        return DjangoUser(
            id=domain_user.id,
            email=domain_user.email,
            username=domain_user.username,
            password_hash=domain_user.password_hash,
            is_active=domain_user.is_active,
            created_at=getattr(domain_user, 'created_at', None)
        )
    
    @staticmethod
    def _to_domain(django_user: DjangoUser) -> DomainUser:
        """
        Convierte un modelo Django a entidad de dominio.
        
        Args:
            django_user: Modelo Django
            
        Returns:
            Entidad de dominio
        """
        return DomainUser(
            id=str(django_user.id),
            email=django_user.email,
            username=django_user.username,
            password_hash=django_user.password_hash,
            is_active=django_user.is_active,
            created_at=django_user.created_at
        )
