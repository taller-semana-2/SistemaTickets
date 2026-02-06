Notification service

This service listens to `ticket_created` events on RabbitMQ and stores simple
Notification records in the PostgreSQL database.

Run locally (after building images and having `db` and `rabbitmq` up):

    docker compose build notification-service
    docker compose up -d db rabbitmq
    docker compose up notification-service
