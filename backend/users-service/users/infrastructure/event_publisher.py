"""
infrastructure/event_publisher.py

🎯 PROPÓSITO:
Implementa la interfaz EventPublisher usando RabbitMQ (pika).

📐 ESTRUCTURA:
- Implementa el método publish() definido en domain/event_publisher.py
- Maneja la conexión y publicación a RabbitMQ
- Serializa los eventos a JSON

✅ EJEMPLO de lo que DEBE ir aquí:
    import json
    import pika
    from dataclasses import asdict
    from users.domain.event_publisher import EventPublisher
    from typing import Any
    
    class RabbitMQEventPublisher(EventPublisher):
        '''Implementación del publicador de eventos usando RabbitMQ'''
        
        def __init__(self, host: str = 'localhost', exchange: str = 'users_events'):
            self.host = host
            self.exchange = exchange
            self._connection = None
            self._channel = None
        
        def _ensure_connection(self):
            '''Establece conexión a RabbitMQ si no está activa'''
            if self._connection is None or self._connection.is_closed:
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host)
                )
                self._channel = self._connection.channel()
                self._channel.exchange_declare(
                    exchange=self.exchange,
                    exchange_type='topic',
                    durable=True
                )
        
        def publish(self, event: Any, routing_key: str) -> None:
            '''Publica un evento de dominio en RabbitMQ'''
            self._ensure_connection()
            
            # Serializar evento a JSON
            if hasattr(event, '__dataclass_fields__'):  # Es un dataclass
                event_data = asdict(event)
            else:
                event_data = event.__dict__
            
            # Convertir datetime a string ISO
            for key, value in event_data.items():
                if hasattr(value, 'isoformat'):
                    event_data[key] = value.isoformat()
            
            message = json.dumps(event_data)
            
            # Publicar
            self._channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    content_type='application/json'
                )
            )
            
            print(f"[x] Evento publicado: {routing_key}")
        
        def close(self):
            '''Cierra la conexión a RabbitMQ'''
            if self._connection and not self._connection.is_closed:
                self._connection.close()

💡 El event publisher desacopla el dominio de la tecnología de mensajería.
   Podríamos cambiar a Kafka sin tocar el dominio.
"""
