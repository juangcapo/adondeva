import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development the API runs on uvicorn; in production FastAPI serves dist/ itself.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
