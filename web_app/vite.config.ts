import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  base: '/registry-review/',
  plugins: [
    tailwindcss(),
    react(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    // Serve PDFs from the examples directory for testing
    fs: {
      allow: [
        // Allow serving files from the project root
        '..',
        // Allow serving PDF files from examples directory
        '../../examples',
      ],
    },
  },
  optimizeDeps: {
    include: ['pdfjs-dist'],
  },
  build: {
    target: 'esnext',
    sourcemap: true,
  },
})
