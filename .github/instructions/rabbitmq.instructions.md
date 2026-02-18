
# RabbitMQ Consumer Standards

---
name: RabbitMQ Messaging Rules
description: Estándares de arquitectura event-driven
applyTo: "**/messaging/**/*.py"
---

## Mandatory Consumer Structure

Consumer must:

- auto reconnect on failure
- validate JSON safely
- log errors
- retry transient failures


---

## Event Schema Standard

Every event must contain:

- event_type (string)
- timestamp (ISO)
- payload object

Reject invalid messages.


---

## Idempotency

Consumers must support duplicate messages.

Never assume message processed once.


---

## Dead Letter Strategy

If message fails permanently:

- send to DLQ
- log full payload
