<template>
    <div class="phone-scanner-view">
        <div class="header">
            <h1>📱 Телефон как сканер</h1>
            <p>Подключитесь к компьютеру и сканируйте QR-коды товаров</p>
        </div>

        <!-- Шаг 1: Подключение к компьютеру -->
        <div v-if="!isConnected" class="connect-section">
            <div class="connect-card">
                <h3>Шаг 1: Подключение к компьютеру</h3>

                <div class="connection-methods">
                    <!-- Метод 1: Ввод ID вручную -->
                    <div class="method manual-input-method">
                        <h4>🔢 Введите 6-значный код</h4>
                        <p>Код отображается на компьютере рядом с QR-кодом</p>
                        <div class="input-group">
                            <input v-model="manualSessionId" placeholder="123456" maxlength="6" inputmode="numeric"
                                pattern="[0-9]*" class="session-input" />
                            <button @click="connectManually" class="btn btn-primary">
                                Подключиться
                            </button>
                        </div>
                    </div>

                    <!-- Метод 2: Сфотографировать QR-код -->
                    <div class="method photo-method">
                        <h4>📸 Сфотографируйте QR-код</h4>
                        <p>Наведите камеру на QR-код с компьютера</p>

                        <div v-if="!isTakingPhoto" class="camera-preview-placeholder">
                            <div class="placeholder-icon">📷</div>
                            <p>Нажмите кнопку ниже для фото</p>
                        </div>

                        <div v-else class="camera-preview">
                            <video ref="videoElement" autoplay playsinline class="camera-video"></video>
                            <div class="photo-overlay">
                                <div class="photo-frame">
                                    <div class="corner corner-tl"></div>
                                    <div class="corner corner-tr"></div>
                                    <div class="corner corner-bl"></div>
                                    <div class="corner corner-br"></div>
                                </div>
                            </div>
                        </div>

                        <div class="photo-controls">
                            <input type="file" ref="fileInput" accept="image/*" capture="environment"
                                @change="handleFileUpload" class="file-input" />

                            <button @click="takePhoto" class="btn btn-primary btn-lg">
                                {{ isTakingPhoto ? '📸 Сделать фото' : '📷 Открыть камеру' }}
                            </button>

                            <div v-if="uploading" class="upload-progress">
                                <div class="progress-bar">
                                    <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
                                </div>
                                <span>Загрузка: {{ uploadProgress }}%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div v-if="connectionError" class="error-message">
                    ❌ {{ connectionError }}
                </div>
            </div>
        </div>

        <!-- Шаг 2: Сканирование товаров -->
        <div v-else class="scanner-section">
            <div class="connection-info">
                <div class="info-card">
                    <h3>✅ Подключено к компьютеру</h3>
                    <div class="session-info">
                        <strong>Сессия:</strong> {{ currentSessionId }}
                        <button @click="disconnect" class="btn-small btn-outline">✖️ Выйти</button>
                    </div>
                    <div class="connection-stats">
                        <span class="stat">📊 Отправлено: {{ successfulScans }}</span>
                        <span class="stat">🕒 Время: {{ formatDuration(connectionTime) }}</span>
                    </div>
                </div>
            </div>

            <div class="product-scanner">
                <h3>Шаг 2: Сканируйте товары</h3>

                <div class="scanner-options">
                    <!-- Опция 1: Сделать фото QR-кода товара -->
                    <div class="scanner-option">
                        <h4>📸 Сфотографировать QR-код товара</h4>
                        <p>Наведите камеру на QR-код товара и сделайте фото</p>

                        <div class="photo-scanner">
                            <input type="file" ref="productFileInput" accept="image/*" capture="environment"
                                @change="scanProductPhoto" class="file-input" />

                            <button @click="openProductCamera" class="btn btn-primary btn-lg">
                                📷 Сфотографировать QR-код
                            </button>
                        </div>
                    </div>

                    <!-- Опция 2: Тестовое сканирование -->
                    <div class="scanner-option">
                        <h4>🧪 Тестовое сканирование</h4>
                        <p>Протестируйте подключение без реального QR-кода</p>

                        <button @click="testScan" class="btn btn-secondary">
                            🔍 Тестовый QR-код
                        </button>

                        <div class="test-input">
                            <input v-model="testQrContent" placeholder="Введите тестовый код" />
                            <button @click="sendTestCode" class="btn btn-info">
                                📤 Отправить
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- История сканирований -->
            <div class="scans-log">
                <h4>📋 История сканирований:</h4>
                <div v-if="scans.length === 0" class="empty-scans">
                    <p>Сфотографируйте QR-код товара для отправки на печать</p>
                </div>
                <div v-else class="scans-list">
                    <div v-for="(scan, index) in scans" :key="index" class="scan-item">
                        <span class="scan-time">{{ formatTime(scan.timestamp) }}</span>
                        <span class="scan-content">{{ truncateText(scan.content, 20) }}</span>
                        <span :class="['scan-status', scan.sent ? 'status-sent' : 'status-error']">
                            {{ scan.sent ? '✓' : '✗' }}
                        </span>
                        <button @click="resendScan(index)" class="btn-small" title="Отправить повторно">
                            🔄
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Статус бар -->
        <div class="status-bar">
            <div class="status-item">
                <span class="status-icon">{{ isConnected ? '📱✅' : '📱' }}</span>
                <span class="status-text">{{ isConnected ? 'Подключено' : 'Не подключено' }}</span>
            </div>
            <div class="status-item">
                <span class="status-icon">📊</span>
                <span class="status-text">{{ successfulScans }} сканов</span>
            </div>
            <div class="status-item">
                <span class="status-icon">⏱️</span>
                <span class="status-text">{{ formatDuration(connectionTime) }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'

const videoElement = ref(null)
const fileInput = ref(null)
const productFileInput = ref(null)
const isConnected = ref(false)
const isTakingPhoto = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const manualSessionId = ref('')
const currentSessionId = ref('')
const connectionError = ref('')
const scans = ref([])
const connectionTime = ref(0)
const testQrContent = ref('TEST-' + Date.now())

let connectCameraStream = null
let wsConnection = null
let connectionTimer = null

const successfulScans = computed(() => {
    return scans.value.filter(scan => scan.sent).length
})

onMounted(() => {
    // Проверяем URL параметры для авто-подключения
    const urlParams = new URLSearchParams(window.location.search)
    const sessionParam = urlParams.get('session')

    if (sessionParam && /^\d{6}$/.test(sessionParam)) {
        manualSessionId.value = sessionParam
        setTimeout(() => connectManually(), 500)
    }
})

onUnmounted(() => {
    stopCamera()
    disconnectWebSocket()
    if (connectionTimer) clearInterval(connectionTimer)
})

const takePhoto = async () => {
    if (!isTakingPhoto.value) {
        await startCamera()
    } else {
        fileInput.value?.click()
    }
}

const startCamera = async () => {
    try {
        if (connectCameraStream) {
            connectCameraStream.getTracks().forEach(track => track.stop())
        }

        const constraints = {
            video: {
                facingMode: { ideal: 'environment' },
                width: { ideal: 1280 },
                height: { ideal: 1280 }
            }
        }

        connectCameraStream = await navigator.mediaDevices.getUserMedia(constraints)

        if (videoElement.value) {
            videoElement.value.srcObject = connectCameraStream
            await videoElement.value.play()
            isTakingPhoto.value = true
        }
    } catch (error) {
        console.error('Camera error:', error)
        connectionError.value = `Ошибка камеры: ${error.message}`
    }
}

const stopCamera = () => {
    if (connectCameraStream) {
        connectCameraStream.getTracks().forEach(track => track.stop())
        connectCameraStream = null
    }
    if (videoElement.value) {
        videoElement.value.srcObject = null
    }
    isTakingPhoto.value = false
}

const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    await processPhotoUpload(file, 'connect')
    stopCamera()
}

const processPhotoUpload = async (file, type) => {
    try {
        uploading.value = true
        uploadProgress.value = 0

        const formData = new FormData()
        formData.append('file', file)

        if (type === 'connect') {
            formData.append('type', 'session_connect')
        }

        const response = await axios.post('/api/photo-scanner/scan-qr/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
                if (progressEvent.total) {
                    uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                }
            }
        })

        uploading.value = false

        if (response.data.success) {
            if (response.data.type === 'session_connect') {
                // Нашли QR-код сессии
                const sessionId = response.data.session_id
                if (sessionId) {
                    await connectToSession(sessionId)
                }
            } else if (response.data.qr_content) {
                // Нашли QR-код товара
                await sendQrCode(response.data.qr_content)
            }

            playSuccessBeep()
        } else {
            connectionError.value = response.data.message || 'QR-код не найден на фото'
            playErrorBeep()
        }

    } catch (error) {
        console.error('Upload error:', error)
        uploading.value = false
        connectionError.value = 'Ошибка загрузки фото'
        playErrorBeep()
    }
}

const connectManually = () => {
    const sessionId = manualSessionId.value.trim()
    if (/^\d{6}$/.test(sessionId)) {
        connectToSession(sessionId)
    } else {
        connectionError.value = 'Введите 6 цифр (например: 123456)'
    }
}

const connectToSession = async (sessionId) => {
    try {
        console.log('Подключение к сессии:', sessionId)

        currentSessionId.value = sessionId
        connectionError.value = ''

        // Сначала проверяем сессию через API
        const checkResponse = await axios.post(`/api/photo-scanner/connect/${sessionId}`)

        if (!checkResponse.data.success) {
            connectionError.value = checkResponse.data.message || 'Ошибка подключения'
            return
        }

        // Подключаемся через WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.hostname
        const port = window.location.port ? `:${window.location.port}` : ''
        const wsUrl = `${protocol}//${host}${port}/ws/remote-scanner/${sessionId}/client`

        console.log('WebSocket URL:', wsUrl)

        if (wsConnection) {
            wsConnection.close()
        }

        wsConnection = new WebSocket(wsUrl)

        wsConnection.onopen = () => {
            console.log('✅ WebSocket подключен')
            isConnected.value = true
            startConnectionTimer()
            playSuccessBeep()

            // Отправляем приветственное сообщение
            wsConnection.send(JSON.stringify({
                type: 'connect',
                session_id: sessionId,
                device_type: 'client'
            }))

            connectionError.value = ''
        }

        wsConnection.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data)
                console.log('📨 Получено:', message)
            } catch (error) {
                console.error('Ошибка парсинга:', error)
            }
        }

        wsConnection.onerror = (error) => {
            console.error('❌ WebSocket ошибка:', error)
            connectionError.value = 'Ошибка подключения к компьютеру'
            resetConnection()
        }

        wsConnection.onclose = () => {
            console.log('📡 WebSocket закрыт')
            resetConnection()
        }

    } catch (error) {
        console.error('❌ Ошибка подключения:', error)
        connectionError.value = `Ошибка: ${error.message}`
        resetConnection()
    }
}

const resetConnection = () => {
    isConnected.value = false
    currentSessionId.value = ''
    connectionTime.value = 0
    if (connectionTimer) {
        clearInterval(connectionTimer)
        connectionTimer = null
    }
}

const startConnectionTimer = () => {
    if (connectionTimer) clearInterval(connectionTimer)

    connectionTime.value = 0
    connectionTimer = setInterval(() => {
        connectionTime.value++
    }, 1000)
}

const openProductCamera = () => {
    productFileInput.value?.click()
}

const scanProductPhoto = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    await processPhotoUpload(file, 'product')
}

const sendQrCode = async (qrContent) => {
    const timestamp = new Date()

    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        try {
            await wsConnection.send(JSON.stringify({
                type: 'scan',
                qr_content: qrContent,
                timestamp: timestamp.toISOString()
            }))

            scans.value.unshift({
                content: qrContent,
                timestamp: timestamp,
                sent: true
            })

            playScanBeep()
            console.log(`📤 Отправлен код: ${qrContent}`)

        } catch (error) {
            console.error('❌ Ошибка отправки:', error)
            scans.value.unshift({
                content: qrContent,
                timestamp: timestamp,
                sent: false
            })
        }
    } else {
        console.warn('⚠️ WebSocket не подключен')
        scans.value.unshift({
            content: qrContent,
            timestamp: timestamp,
            sent: false
        })
    }

    // Ограничиваем историю
    if (scans.value.length > 20) {
        scans.value = scans.value.slice(0, 20)
    }
}

const testScan = () => {
    const testCode = `TEST-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`
    sendQrCode(testCode)
}

const sendTestCode = () => {
    if (testQrContent.value.trim()) {
        sendQrCode(testQrContent.value.trim())
        testQrContent.value = `TEST-${Date.now()}`
    }
}

const resendScan = (index) => {
    if (index >= 0 && index < scans.value.length) {
        const scan = scans.value[index]
        sendQrCode(scan.content)
    }
}

const disconnect = () => {
    if (wsConnection) {
        wsConnection.close(1000, 'Пользователь отключился')
    }
    disconnectWebSocket()
    resetConnection()
}

const disconnectWebSocket = () => {
    if (wsConnection) {
        wsConnection.close()
        wsConnection = null
    }
    isConnected.value = false
    scans.value = []
}

const playSuccessBeep = () => {
    playBeep(800, 0.2)
}

const playScanBeep = () => {
    playBeep(1200, 0.1)
}

const playErrorBeep = () => {
    playBeep(400, 0.3)
}

const playBeep = (frequency, duration) => {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()

        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)

        oscillator.frequency.value = frequency
        oscillator.type = 'sine'

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration)

        oscillator.start(audioContext.currentTime)
        oscillator.stop(audioContext.currentTime + duration)
    } catch (e) {
        console.log('🔇 Аудио не поддерживается')
    }
}

const truncateText = (text, maxLength) => {
    if (!text) return ''
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
}

const formatTime = (date) => {
    if (!date) return ''
    const d = date instanceof Date ? date : new Date(date)
    return d.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })
}

const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* Основные стили остаются, добавляем новые */
.phone-scanner-view {
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
}

.connection-methods {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    margin: 2rem 0;
}

.method {
    background: rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.method h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    font-size: 1.2rem;
}

.input-group {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.session-input {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    font-size: 1.2rem;
    text-align: center;
    letter-spacing: 2px;
}

.camera-preview-placeholder {
    text-align: center;
    padding: 2rem;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    margin: 1rem 0;
}

.placeholder-icon {
    font-size: 3rem;
    opacity: 0.5;
}

.camera-preview {
    position: relative;
    width: 100%;
    height: 300px;
    border-radius: 12px;
    overflow: hidden;
    background: black;
    margin: 1rem 0;
}

.camera-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.photo-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    pointer-events: none;
}

.photo-frame {
    width: 70%;
    height: 70%;
    border: 3px solid rgba(40, 167, 69, 0.8);
    border-radius: 12px;
    position: relative;
    box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.7);
}

.corner {
    position: absolute;
    width: 24px;
    height: 24px;
    border: 3px solid #28a745;
}

.corner-tl {
    top: -3px;
    left: -3px;
    border-right: none;
    border-bottom: none;
    border-top-left-radius: 8px;
}

.corner-tr {
    top: -3px;
    right: -3px;
    border-left: none;
    border-bottom: none;
    border-top-right-radius: 8px;
}

.corner-bl {
    bottom: -3px;
    left: -3px;
    border-right: none;
    border-top: none;
    border-bottom-left-radius: 8px;
}

.corner-br {
    bottom: -3px;
    right: -3px;
    border-left: none;
    border-top: none;
    border-bottom-right-radius: 8px;
}

.photo-controls {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
}

.file-input {
    display: none;
}

.upload-progress {
    width: 100%;
    max-width: 300px;
    text-align: center;
}

.progress-bar {
    width: 100%;
    height: 10px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.progress-fill {
    height: 100%;
    background: #28a745;
    transition: width 0.3s;
}

.error-message {
    background: rgba(220, 53, 69, 0.2);
    border: 1px solid #dc3545;
    color: #ff6b6b;
    padding: 1rem;
    border-radius: 8px;
    margin-top: 1rem;
}

.product-scanner {
    margin: 2rem 0;
}

.scanner-options {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin-top: 1rem;
}

.scanner-option {
    background: rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    border-radius: 12px;
}

.test-input {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.test-input input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
}

.btn-small {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
}

.btn-outline {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-outline:hover {
    background: rgba(255, 255, 255, 0.1);
}

.btn-lg {
    padding: 1rem 2rem;
    font-size: 1.1rem;
}

.scan-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    gap: 1rem;
}

.scan-item button {
    opacity: 0.7;
    transition: opacity 0.2s;
}

.scan-item button:hover {
    opacity: 1;
}
</style>