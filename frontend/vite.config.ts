import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    // Build straight into the backend so Flask can serve the SPA (single-origin deploy).
    outDir: '../backend/webdist',
    emptyOutDir: true,
  },
  server: {
    // In dev the SPA runs on :5173; forward API calls to the Flask backend on :5000
    // so the frontend can use relative "/api/..." paths in both dev and production.
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
})
