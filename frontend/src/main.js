import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// Настраиваем базовый URL для axios
const apiUrl = import.meta.env.VITE_API_URL || '/api';
axios.defaults.baseURL = apiUrl;

// Настраиваем заголовки по умолчанию
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.headers.common['Accept'] = 'application/json';

// Добавляем интерцептор для обработки ошибок
axios.interceptors.response.use(
    response => response,
    error => {
        console.error('API Error:', error);
        return Promise.reject(error);
    }
);

const app = createApp(App);

app.use(router);

// Добавляем глобальные свойства
app.config.globalProperties.$apiUrl = apiUrl;
app.config.globalProperties.$appName = import.meta.env.VITE_APP_NAME || 'QR System';

app.mount('#app');