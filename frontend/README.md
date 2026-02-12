# Sistema de Tickets - Frontend

Frontend del sistema de tickets construido con React, TypeScript y Vite.

## 🚀 Tecnologías

- **React 19** - Framework UI
- **TypeScript** - Tipado estático
- **Vite** - Build tool y dev server
- **React Router v7** - Navegación
- **Axios** - Cliente HTTP

## 📁 Estructura

```
src/
├── api/           # Clientes API (Axios)
├── components/    # Componentes reutilizables
├── pages/         # Páginas/Vistas
├── routes/        # Configuración de rutas
└── types/         # Tipos TypeScript
```

## 🔐 Autenticación

El sistema incluye páginas de autenticación modernas:

- **`/login`** - Inicio de sesión (email, password)
- **`/register`** - Registro de usuario (nombre, email, password)

## 🛣️ Rutas principales

- `/` → Redirige a `/login`
- `/login` → Página de inicio de sesión
- `/register` → Página de registro
- `/tickets` → Lista de tickets
- `/tickets/new` → Crear nuevo ticket
- `/tickets/:id` → Detalle de ticket
- `/notifications` → Lista de notificaciones
- `/assignments` → Lista de asignaciones

## 🎨 Características de diseño

- Diseño moderno con gradientes y animaciones
- Fondo animado con efectos de blur
- Formularios con validación en tiempo real
- Estados de carga y error
- Responsive design
- Transiciones suaves

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
