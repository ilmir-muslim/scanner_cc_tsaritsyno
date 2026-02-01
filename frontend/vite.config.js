import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'url'

export default defineConfig(({ mode, command }) => {
  // Загружаем все переменные окружения
  const env = loadEnv(mode, process.cwd(), '')

  // Определяем, находимся ли мы внутри Docker контейнера
  const isDocker = process.env.IS_DOCKER || env.IS_DOCKER || false

  // Определяем целевой URL для бэкенда
  const getBackendUrl = () => {
    // Если есть явная настройка - используем её
    if (env.VITE_BACKEND_URL) {
      return env.VITE_BACKEND_URL
    }

    // Если в режиме разработки внутри Docker
    if (command === 'serve' && isDocker) {
      return 'http://backend:8003'
    }

    // Для продакшена используем хардкод (или переменную)
    if (mode === 'production') {
      return 'http://46.23.98.207:8003'  // или env.VITE_PROD_BACKEND_URL
    }

    // По умолчанию для локальной разработки
    return 'http://localhost:8003'
  }

  const backendUrl = getBackendUrl()
  const wsUrl = backendUrl.replace('http://', 'ws://').replace('https://', 'wss://')

  return {
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
          target: backendUrl,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '/api')
        },
        '/ws': {
          target: wsUrl,
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
            scanner: ['jsqr']
          }
        }
      }
    },
    // Передаем переменные в код приложения
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || '/api')
    }
  }
})