import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // read VITE_* keys from the single .env file in the project root
  envDir: '..',
  server: {
    // the FastAPI backend runs on port 8000; /api calls are forwarded to it
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
