import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// Функция для автоматического определения URL API
const getApiBaseUrl = () => {
    // Если есть явная настройка - используем её
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL
    }

    // Автоматическое определение для продакшена
    const { protocol, hostname, port } = window.location

    // Если мы на сервере в продакшене
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        // Если порт 80/443 не указываем порт
        const portPart = (port && port !== '80' && port !== '443') ? `:${port}` : ''
        return `${protocol}//${hostname}${portPart}/api`
    }

    // Для локальной разработки
    return 'http://localhost:8003/api'
}

// Настраиваем axios
const apiUrl = getApiBaseUrl()
axios.defaults.baseURL = apiUrl

console.log(`🚀 API Base URL: ${apiUrl}`)
console.log(`🌍 Environment: ${import.meta.env.MODE}`)

// Настраиваем заголовки по умолчанию
axios.defaults.headers.common['Content-Type'] = 'application/json'
axios.defaults.headers.common['Accept'] = 'application/json'

// Добавляем интерцептор для обработки ошибок
axios.interceptors.response.use(
    response => response,
    error => {
        console.error('API Error:', error)
        return Promise.reject(error)
    }
)

const app = createApp(App)
app.use(router)

// Добавляем глобальные свойства
app.config.globalProperties.$apiUrl = apiUrl
app.config.globalProperties.$appName = import.meta.env.VITE_APP_NAME || 'QR System'

app.mount('#app')