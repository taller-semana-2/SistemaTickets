"""
infrastructure/repository.py

🎯 PROPÓSITO:
Implementa la interfaz UserRepository usando Django ORM.

📐 ESTRUCTURA:
- Implementa TODOS los métodos abstractos de domain/repositories.py
- Traduce entre entidades de dominio y modelos de Django
- Maneja la persistencia en base de datos

✅ EJEMPLO de lo que DEBE ir aquí:
    from typing import Optional, List
    from users.domain.repositories import UserRepository
    from users.domain.entities import User as UserEntity
    from users.models import User as UserModel  # Modelo Django
    
    class DjangoUserRepository(UserRepository):
        '''Implementación del repositorio usando Django ORM'''
        
        def save(self, user: UserEntity) -> UserEntity:
            '''Persiste una entidad User en la base de datos'''
            # Traducir entidad de dominio -> modelo Django
            user_model, created = UserModel.objects.update_or_create(
                id=user.id,
                defaults={
                    'email': user.email,
                    'username': user.username,
                    'is_active': user.is_active,
                }
            )
            # Devolver entidad actualizada
            return self._to_entity(user_model)
        
        def find_by_id(self, user_id: str) -> Optional[UserEntity]:
            '''Busca un usuario por ID'''
            try:
                user_model = UserModel.objects.get(id=user_id)
                return self._to_entity(user_model)
            except UserModel.DoesNotExist:
                return None
        
        def find_by_email(self, email: str) -> Optional[UserEntity]:
            '''Busca un usuario por email'''
            try:
                user_model = UserModel.objects.get(email=email)
                return self._to_entity(user_model)
            except UserModel.DoesNotExist:
                return None
        
        def find_all(self) -> List[UserEntity]:
            '''Devuelve todos los usuarios'''
            user_models = UserModel.objects.all()
            return [self._to_entity(um) for um in user_models]
        
        def exists_by_email(self, email: str) -> bool:
            '''Verifica si existe un usuario con ese email'''
            return UserModel.objects.filter(email=email).exists()
        
        def _to_entity(self, user_model: UserModel) -> UserEntity:
            '''Convierte un modelo Django en una entidad de dominio'''
            return UserEntity(
                id=str(user_model.id),
                email=user_model.email,
                username=user_model.username,
                is_active=user_model.is_active
            )

💡 El repositorio es el PUENTE entre el dominio puro y Django ORM.
   Oculta los detalles de persistencia al dominio.
"""
