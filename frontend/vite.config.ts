import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // Mirrors the "@/*" path in tsconfig so Vite and TypeScript agree.
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
})
