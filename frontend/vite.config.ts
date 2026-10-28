import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, Vite serves the UI and forwards /api to the Python backend.
// In normal use, the backend serves the built UI from dist/ itself.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    proxy: {
      '/api': 'http://127.0.0.1:8765',
    },
  },
})
