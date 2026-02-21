# React Frontend Rules

---
name: React Frontend Rules
description: Estándares para frontend React + TypeScript
applyTo: "frontend/**/*.{ts,tsx}"
---

## Project Structure Rules

- Use feature-based structure (features/, shared/, services/, hooks/)
- Avoid dumping components in a flat structure
- Keep concerns separated (UI, state, API, logic)

---

## Component Rules

- Use functional components only
- Keep components under 250 lines
- Separate UI from business logic
- Move API calls to services/

Never call axios or fetch directly inside components.

---

## API Rules

Use dedicated API clients:

- ticketApi
- usersApi
- notificationApi

All API clients must:

- Use a shared axios instance
- Handle errors centrally
- Never hardcode URLs
- Rely on environment variables

Do not create inline fetch/axios calls.

---

## State Management Rules

- Keep state local when possible
- Use Context only for low-frequency global state (e.g., auth)
- Avoid prop drilling
- Avoid placing frequently updating state in Context

---

## TypeScript Rules

- Never use `any`
- Define interfaces/types for API responses
- Type all component props explicitly
- Use strict typing

---

## Security Rules

Never:

- Store JWT in localStorage
- Expose backend ports or service names in code
- Trust frontend-only validation

Always:

- Use environment configuration
- Sanitize user inputs
- Prefer httpOnly cookies for authentication when possible

---

## Testing Rules

- Business logic must be testable
- Prefer React Testing Library
- Avoid testing implementation details

---