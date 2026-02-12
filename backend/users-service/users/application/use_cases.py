"""
application/use_cases.py

🎯 PROPÓSITO:
Implementa los casos de uso del sistema (flujos completos de negocio).

📐 ESTRUCTURA:
- Cada clase = UN caso de uso específico
- Reciben dependencias por inyección (repositorios, event publisher)
- Coordinan entidades, factories y repositorios
- Devuelven resultados o lanzan excepciones de dominio

✅ EJEMPLO de lo que DEBE ir aquí:
    from users.domain.repositories import UserRepository
    from users.domain.event_publisher import EventPublisher
    from users.domain.factories import UserFactory
    from users.domain.events import UserCreated
    from users.domain.exceptions import UserAlreadyExists
    from datetime import datetime
    
    class CreateUserUseCase:
        '''Caso de uso: Crear un nuevo usuario'''
        
        def __init__(self, repository: UserRepository, event_publisher: EventPublisher):
            self.repository = repository
            self.event_publisher = event_publisher
        
        def execute(self, email: str, username: str, password: str):
            # 1. Validar que no exista
            if self.repository.exists_by_email(email):
                raise UserAlreadyExists(email)
            
            # 2. Crear entidad válida usando factory
            user = UserFactory.create(email, username, password)
            
            # 3. Persistir
            saved_user = self.repository.save(user)
            
            # 4. Publicar evento de dominio
            event = UserCreated(
                user_id=saved_user.id,
                email=saved_user.email,
                username=saved_user.username,
                occurred_at=datetime.now()
            )
            self.event_publisher.publish(event, routing_key='user.created')
            
            # 5. Devolver resultado
            return saved_user
    
    class DeactivateUserUseCase:
        '''Caso de uso: Desactivar un usuario existente'''
        
        def __init__(self, repository: UserRepository, event_publisher: EventPublisher):
            self.repository = repository
            self.event_publisher = event_publisher
        
        def execute(self, user_id: str, reason: str):
            # 1. Recuperar entidad
            user = self.repository.find_by_id(user_id)
            if not user:
                raise UserNotFound(user_id)
            
            # 2. Ejecutar lógica de dominio
            user.deactivate()  # Puede lanzar UserAlreadyInactive
            
            # 3. Persistir cambios
            updated_user = self.repository.save(user)
            
            # 4. Publicar evento
            event = UserDeactivated(
                user_id=user.id,
                reason=reason,
                occurred_at=datetime.now()
            )
            self.event_publisher.publish(event, routing_key='user.deactivated')
            
            return updated_user

💡 Los Use Cases son SIMPLES: coordinan, NO implementan lógica de negocio compleja.
"""
