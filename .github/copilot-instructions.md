# Copilot instructions for SistemaTickets

## Big picture
- Backend is organized as service folders under backend/: assignment-service, notification-service, and ticket-service. Only ticket-service currently contains code; the other folders are empty placeholders for future microservices.
- ticket-service is a Django project (project package ticket_service) with a single app tickets and a single model `Ticket` (title/description/status/created_at). See [backend/ticket-service/tickets/models.py](backend/ticket-service/tickets/models.py).
- REST framework is installed in settings, but no API views or routes are defined yet (urls only contains the admin route). See [backend/ticket-service/ticket_service/settings.py](backend/ticket-service/ticket_service/settings.py) and [backend/ticket-service/ticket_service/urls.py](backend/ticket-service/ticket_service/urls.py).
- Messaging integration is planned via a messaging package with pika in dependencies; current messaging modules are empty stubs. See [backend/ticket-service/messaging](backend/ticket-service/messaging) and [backend/ticket-service/requirements.txt](backend/ticket-service/requirements.txt).

## Data & dependencies
- Database is SQLite at backend/ticket-service/db.sqlite3 configured via Django settings. See [backend/ticket-service/ticket_service/settings.py](backend/ticket-service/ticket_service/settings.py).
- Python dependencies are pinned in requirements.txt; include Django, djangorestframework, and pika. See [backend/ticket-service/requirements.txt](backend/ticket-service/requirements.txt).

## Developer workflows (ticket-service)
- Run Django management commands from backend/ticket-service/ using manage.py. See [backend/ticket-service/manage.py](backend/ticket-service/manage.py).
- Typical lifecycle when adding models: create migrations and migrate before running the dev server.

## Conventions & patterns
- Keep Django app code under backend/ticket-service/tickets/; project-level config stays in backend/ticket-service/ticket_service/.
- If adding API endpoints, update project URLs in [backend/ticket-service/ticket_service/urls.py](backend/ticket-service/ticket_service/urls.py) and implement views in [backend/ticket-service/tickets/views.py](backend/ticket-service/tickets/views.py).
- Messaging-related code should live under backend/ticket-service/messaging/; there are placeholder modules for events and RabbitMQ transport.
