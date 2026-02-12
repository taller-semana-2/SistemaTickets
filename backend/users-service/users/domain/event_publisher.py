"""
domain/event_publisher.py

🎯 PROPÓSITO:
Define la INTERFAZ para publicar eventos de dominio.

⚠️ IMPORTANTE: Este archivo contiene SOLO la interfaz abstracta.
La IMPLEMENTACIÓN (RabbitMQ, etc.) va en infrastructure/event_publisher.py

📐 ESTRUCTURA:
- Interfaz abstracta que define el contrato de publicación
- NO contiene lógica de mensajería real
- Permite cambiar la implementación sin afectar el dominio

✅ EJEMPLO de lo que DEBE ir aquí:
    from abc import ABC, abstractmethod
    from typing import Any
    
    class EventPublisher(ABC):
        '''Contrato para publicar eventos de dominio'''
        
        @abstractmethod
        def publish(self, event: Any, routing_key: str) -> None:
            '''
            Publica un evento de dominio.
            
            Args:
                event: El evento a publicar (UserCreated, UserDeactivated, etc.)
                routing_key: Clave de enrutamiento para el mensaje
            '''
            pass

💡 El dominio solo sabe que puede "publicar eventos", no sabe CÓMO se publican.
"""
