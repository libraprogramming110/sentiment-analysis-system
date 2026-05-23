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
})
