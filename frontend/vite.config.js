import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backend = process.env.VITE_BACKEND_URL || 'http://localhost:8000'
const gradesBackend = process.env.VITE_GRADES_BACKEND_URL || 'http://localhost:8001'

const proxy = {
  '/api': { target: backend, changeOrigin: true },
  '/grades-api': {
    target: gradesBackend,
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/grades-api/, '/api'),
  },
}

export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
})
