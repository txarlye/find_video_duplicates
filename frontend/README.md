# Frontend

React + Vite + TypeScript, sustituyendo a Streamlit pantalla a pantalla
(ver el plan de migración). Mantine para componentes, TanStack Query
para el estado de servidor, React Router para las rutas.

## Desarrollo

```bash
npm install
npm run dev
```

Necesita la API corriendo en `:8000` (`python main_api.py` desde la
raíz del repo) — `vite.config.ts` ya tiene el proxy de `/api` y `/ws`
hacia ahí, así que en desarrollo no hace falta lidiar con CORS.

## Build de producción

```bash
npm run build
```

Genera `dist/`, que `src/api/main.py` sirve directamente (sin nginx) si
existe. Dentro de Docker esto lo hace el stage de Node del
`docker/Dockerfile` automáticamente — nunca hace falta ejecutarlo a mano
para desplegar.
