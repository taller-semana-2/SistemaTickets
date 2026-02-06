API para frontend — Notification Service

Endpoints disponibles (desarrollo):

- GET /api/notifications/  → lista las notificaciones (últimas primero)
- GET /api/notifications/{id}/ → detalles de una notificación

Formato de respuesta (ejemplo):

[{"id":1, "ticket_id":"E2E-1", "message":"Ticket E2E-1 creado", "sent_at":"2026-02-06T13:49:24Z"}, ...]

Consideraciones para el frontend:
- CORS está habilitado (para desarrollo) — puedes consumir desde `localhost:5173` sin configuración adicional.
- La API es read-only por ahora; el backend crea notificaciones cuando recibe eventos `ticket_created` desde RabbitMQ.

Recomendación para mostrar notificaciones:
- Hacer un polling cada N segundos a `/api/notifications/` o
- Implementar WebSocket/SSE para recibir notificaciones en tiempo real (requiere añadir Django Channels o un servidor de WebSocket que reciba eventos del consumidor).

Ejemplo de consumo con fetch:

```js
async function loadNotifications() {
  const r = await fetch('http://localhost:8001/api/notifications/');
  const data = await r.json();
  return data;
}
```

Si necesitas que el endpoint tenga paginación o filtros (por ticket_id), dímelo y lo añado.
