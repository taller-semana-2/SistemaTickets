# Backend DDD Rules (Django Microservices)

name: Backend DDD Rules
description: Reglas para microservicios Django (backend)
applyTo: "backend/**/*.py"

## Mandatory Separation

Never place business logic inside:

- serializers.py
- views.py
- messaging handlers

Instead:

View → UseCase → Domain → Repository


---

## Repository Pattern Required

All persistence must go through repositories.

Never:


Model.objects.create()


inside business logic.


---

## Domain Rules

Domain layer:

- must not import Django
- must not import REST framework
- must not import RabbitMQ

Only pure Python allowed.


---

## Messaging Rules

RabbitMQ handlers must:

1. Parse message
2. Validate schema
3. Call use case
4. ACK message

Never implement business decisions inside handler.

---
