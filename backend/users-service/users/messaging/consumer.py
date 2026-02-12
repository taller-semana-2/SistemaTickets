"""
messaging/consumer.py

🎯 PROPÓSITO:
Consume eventos de RabbitMQ publicados por otros microservicios.

📐 ESTRUCTURA:
- Configura conexión a RabbitMQ
- Define colas y bindings
- Escucha eventos específicos
- Delega el procesamiento a los handlers

✅ EJEMPLO de lo que DEBE ir aquí:
    import pika
    import json
    from .handlers import TicketAssignedHandler
    
    class RabbitMQConsumer:
        '''Consumidor de eventos de RabbitMQ'''
        
        def __init__(self, host: str = 'localhost'):
            self.host = host
            self.connection = None
            self.channel = None
            
            # Registrar handlers de eventos
            self.handlers = {
                'ticket.assigned': TicketAssignedHandler(),
                'ticket.closed': TicketClosedHandler(),
            }
        
        def start(self):
            '''Inicia el consumidor y escucha eventos'''
            # Establecer conexión
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()
            
            # Declarar exchange
            self.channel.exchange_declare(
                exchange='tickets_events',
                exchange_type='topic',
                durable=True
            )
            
            # Crear cola para este servicio
            queue = self.channel.queue_declare(
                queue='users_service_queue',
                durable=True
            )
            
            # Binding: escuchar eventos de tickets
            self.channel.queue_bind(
                exchange='tickets_events',
                queue='users_service_queue',
                routing_key='ticket.*'
            )
            
            # Configurar callback
            self.channel.basic_consume(
                queue='users_service_queue',
                on_message_callback=self._on_message,
                auto_ack=False
            )
            
            print('[*] Esperando eventos...')
            self.channel.start_consuming()
        
        def _on_message(self, ch, method, properties, body):
            '''Procesa un mensaje recibido'''
            try:
                # Deserializar evento
                event_data = json.loads(body)
                routing_key = method.routing_key
                
                print(f"[x] Evento recibido: {routing_key}")
                
                # Delegar al handler correspondiente
                handler = self.handlers.get(routing_key)
                if handler:
                    handler.handle(event_data)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    print(f"[!] No hay handler para: {routing_key}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            
            except Exception as e:
                print(f"[ERROR] Procesando evento: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        def stop(self):
            '''Detiene el consumidor'''
            if self.connection:
                self.connection.close()

💡 El consumer es el "listener" que conecta RabbitMQ con tu aplicación.
"""
