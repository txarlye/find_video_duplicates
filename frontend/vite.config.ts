import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo, la API corre aparte (uvicorn en :8000) — el proxy evita
// tener que lidiar con CORS mientras se itera. En producción todo se
// sirve desde el mismo origen (FastAPI monta el build de dist/), así
// que este proxy no se usa nunca fuera de `npm run dev`.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
  },
})
