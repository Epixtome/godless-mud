import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/studio/',
  plugins: [react()],
  server: {
    port: 5175,
    host: '127.0.0.1'
  }
})
