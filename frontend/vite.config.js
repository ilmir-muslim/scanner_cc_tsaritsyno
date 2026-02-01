import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      },
      // WebSocket proxy
      '/ws': {
        target: 'ws://backend:8003',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ws/, '')
      }
    }
  },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'axios'],
          scanner: ['jsqr'],
          qrcode: ['qrcode']
        }
      }
    }
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || '/api')
  }
})