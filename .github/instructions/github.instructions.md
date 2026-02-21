# GitHub Workflow Rules

## Creacion de issues
- Usar el project creado en el repositorio y a partir de ahi crear los issues.
- Cada issue debe incluir:
  - Titulo claro.
  - Contexto (por que se necesita).
  - Objetivo (que se espera lograr).
  - Criterios de aceptacion (formato Gherkin).
  - Consideraciones de testing (que niveles de prueba aplican).
  - Responsable asignado (backend, frontend, QA).
  - Labels (backend, feature, etc.).
  - Issue Type.

## Branching
- Luego de crear el issue, crear una rama a partir del issue y vincularla.
- El nombre de la rama debe seguir Gitflow.

## Commits y pull requests
- Realizar cambios en la rama usando commits atomicos y Conventional Commits.
- Pushear la rama y crear un pull request hacia `develop`.
- El pull request debe:
  - Describir claramente los cambios realizados.
  - Mencionar el issue relacionado.
  - Incluir `Closes #issue_number` para cerrar el issue al hacer merge.
