import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
        '/chainlit': 'http://localhost:8000', // Redirect ke Chainlit
    },
},
})
