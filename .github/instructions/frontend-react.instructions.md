
# React Frontend Rules

---
name: React Frontend Rules
description: Reglas para frontend React + TypeScript
applyTo: "frontend/**/*.{ts,tsx}"
---

## Component Rules

- Prefer functional components
- Keep components under 250 lines
- Move API calls to services/

Never call axios directly inside components.


---

## API Rules

Use dedicated API clients:

ticketApi  
usersApi  
notificationApi  

Do not create inline fetch calls.


---

## State Management

- Prefer Context for global state
- Keep state local when possible
- Avoid prop drilling


---

## Security Rules

Never:

- store JWT in localStorage
- expose backend service ports in code

Always rely on environment config.

---
