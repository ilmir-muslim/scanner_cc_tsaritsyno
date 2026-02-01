<template>
    <div class="phone-scanner-view">
        <div class="header">
            <h1>📱 Камера телефона как сканер</h1>
            <p>Сканируйте QR-коды и отправляйте их на печать на компьютере</p>
        </div>

        <div v-if="!isConnected" class="connect-section">
            <div class="connect-card">
                <h3>Подключение к компьютеру</h3>
                <p>Отсканируйте QR-код с компьютера для подключения</p>

                <div class="camera-preview">
                    <video ref="videoElement" autoplay playsinline class="camera-video"></video>
                    <div class="scan-overlay">
                        <div class="scan-frame">
                            <div class="corner corner-tl"></div>
                            <div class="corner corner-tr"></div>
                            <div class="corner corner-bl"></div>
                            <div class="corner corner-br"></div>
                        </div>
                        <div class="scan-line"></div>
                    </div>
                </div>

                <div class="connection-status">
                    <div v-if="cameraError" class="status-error">
                        <span class="status-icon">❌</span>
                        <span>{{ cameraError }}</span>
                        <button @click="startCamera" class="btn btn-small">Повторить</button>
                    </div>
                    <div v-else-if="isScanning" class="status-scanning">
                        <span class="status-icon">🔍</span>
                        <span>Сканирую QR-код подключения...</span>
                    </div>
                    <div v-else class="status-waiting">
                        <span class="status-icon">📷</span>
                        <span>Наведите камеру на QR-код с компьютера</span>
                        <small>QR-код должен быть полностью в рамке</small>
                    </div>
                </div>

                <div class="manual-connect">
                    <p>Или введите ID подключения вручную (6 цифр):</p>
                    <div class="manual-input">
                        <input v-model="manualSessionId" placeholder="Например: 123456" maxlength="6" pattern="[0-9]*"
                            inputmode="numeric" />
                        <button @click="connectManually" class="btn btn-primary">
                            Подключиться
                        </button>
                    </div>
                    <p class="hint">ID отображается на компьютере рядом с QR-кодом</p>
                </div>
            </div>
        </div>

        <div v-else class="scanner-section">
            <div class="connection-info">
                <div class="info-card">
                    <h3>✅ Подключено к компьютеру</h3>
                    <p>Теперь сканируйте QR-коды товаров</p>
                    <div class="session-info">
                        <strong>ID сессии:</strong> {{ currentSessionId }}
                    </div>
                    <div class="connection-stats">
                        <span class="stat">📊 Сканов отправлено: {{ successfulScans }}</span>
                        <span class="stat">🕒 Подключено: {{ formatDuration(connectionTime) }}</span>
                    </div>
                </div>
            </div>

            <div class="camera-section">
                <div class="camera-controls">
                    <button @click="toggleScannerCamera"
                        :class="['camera-toggle-btn', isScannerActive ? 'btn-danger' : 'btn-success']">
                        {{ isScannerActive ? 'Остановить сканирование' : 'Начать сканирование' }}
                    </button>

                    <button @click="testScan" class="btn btn-info">
                        🔍 Тестовое сканирование
                    </button>

                    <button @click="disconnect" class="btn btn-secondary">
                        ✖️ Отключиться
                    </button>
                </div>

                <div v-if="isScannerActive" class="scanner-preview">
                    <video ref="scannerVideoElement" autoplay playsinline class="scanner-video"></video>
                    <div class="scan-overlay">
                        <div class="scan-frame">
                            <div class="corner corner-tl"></div>
                            <div class="corner corner-tr"></div>
                            <div class="corner corner-bl"></div>
                            <div class="corner corner-br"></div>
                        </div>
                        <div class="scan-line"></div>
                    </div>
                </div>

                <div v-else class="scanner-placeholder">
                    <div class="placeholder-icon">📷</div>
                    <p>Нажмите "Начать сканирование" для активации камеры</p>
                </div>
            </div>

            <div class="scans-log">
                <h4>📋 История сканирований:</h4>
                <div v-if="scans.length === 0" class="empty-scans">
                    <p>Сканируйте QR-коды товаров, чтобы отправить их на печать</p>
                </div>
                <div v-else class="scans-list">
                    <div v-for="(scan, index) in scans" :key="index" class="scan-item">
                        <span class="scan-time">{{ formatTime(scan.timestamp) }}</span>
                        <span class="scan-content">{{ truncateText(scan.content, 20) }}</span>
                        <span :class="['scan-status', scan.sent ? 'status-sent' : 'status-error']">
                            {{ scan.sent ? '✓' : '✗' }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <div class="status-bar">
            <div class="status-item">
                <span class="status-icon">{{ isConnected ? '📱✅' : '📱❌' }}</span>
                <span class="status-text">{{ isConnected ? 'Подключено' : 'Не подключено' }}</span>
            </div>
            <div class="status-item">
                <span class="status-icon">📊</span>
                <span class="status-text">Сканов: {{ successfulScans }}/{{ scans.length }}</span>
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

const videoElement = ref(null)
const scannerVideoElement = ref(null)
const isConnected = ref(false)
const isScanning = ref(false)
const isScannerActive = ref(false)
const cameraError = ref('')
const manualSessionId = ref('')
const currentSessionId = ref('')
const scans = ref([])
const connectionTime = ref(0)

let connectCameraStream = null
let scannerCameraStream = null
let wsConnection = null
let scanInterval = null
let connectionTimer = null

const successfulScans = computed(() => {
    return scans.value.filter(scan => scan.sent).length
})

onMounted(() => {
    startCamera()
})

onUnmounted(() => {
    stopCamera()
    stopScannerCamera()
    disconnectWebSocket()
    if (scanInterval) clearInterval(scanInterval)
    if (connectionTimer) clearInterval(connectionTimer)
})

const startCamera = async () => {
    try {
        cameraError.value = ''

        // Останавливаем предыдущий поток если есть
        if (connectCameraStream) {
            connectCameraStream.getTracks().forEach(track => track.stop())
        }

        // Простые настройки камеры
        const constraints = {
            video: {
                facingMode: { ideal: 'environment' },
                width: { ideal: 640 },
                height: { ideal: 640 }
            },
            audio: false
        }

        connectCameraStream = await navigator.mediaDevices.getUserMedia(constraints)

        if (videoElement.value) {
            videoElement.value.srcObject = connectCameraStream
            await videoElement.value.play()

            // Запускаем сканирование QR-кода подключения
            startQrScanning()
            console.log('📷 Камера запущена')
        }

    } catch (error) {
        console.error('Camera error:', error)
        cameraError.value = `Ошибка камеры: ${error.message}`
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
    if (scanInterval) clearInterval(scanInterval)
    isScanning.value = false
}

const startQrScanning = () => {
    console.log('🔍 Начало сканирования')

    if (scanInterval) clearInterval(scanInterval)

    // Просто проверяем ручной ввод каждую секунду
    scanInterval = setInterval(() => {
        if (manualSessionId.value && /^\d{6}$/.test(manualSessionId.value)) {
            console.log('📱 Ручной ввод обнаружен:', manualSessionId.value)
            connectToSession(manualSessionId.value)
            manualSessionId.value = ''
        }
    }, 1000)
}

const connectManually = () => {
    const sessionId = manualSessionId.value.trim()
    if (/^\d{6}$/.test(sessionId)) {
        connectToSession(sessionId)
    } else {
        alert('Введите 6 цифр (например: 123456)')
    }
}

const connectToSession = async (sessionId) => {
    try {
        console.log('🔄 Подключение к сессии:', sessionId)

        currentSessionId.value = sessionId
        isScanning.value = true

        // Определяем WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.hostname
        const port = window.location.port ? `:${window.location.port}` : ''
        const wsUrl = `${protocol}//${host}${port}/ws/remote-scanner/${sessionId}/client`

        console.log('📡 WebSocket URL:', wsUrl)

        // Закрываем предыдущее соединение
        if (wsConnection) {
            wsConnection.close()
        }

        wsConnection = new WebSocket(wsUrl)

        wsConnection.onopen = () => {
            console.log('✅ WebSocket подключен')
            isConnected.value = true
            isScanning.value = false
            startConnectionTimer()
            playSuccessBeep()

            alert('✅ Успешно подключено! Теперь можно сканировать QR-коды.')
        }

        wsConnection.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data)
                console.log('📨 Получено:', message)

                if (message.type === 'connected') {
                    console.log('✅ Подтверждение подключения')
                }

                if (message.type === 'status') {
                    console.log('📊 Статус:', message.message)
                }

            } catch (error) {
                console.error('❌ Ошибка парсинга:', error)
            }
        }

        wsConnection.onerror = (error) => {
            console.error('❌ WebSocket ошибка:', error)
            alert('Ошибка подключения. Убедитесь, что компьютер ожидает подключения.')
            resetConnection()
        }

        wsConnection.onclose = (event) => {
            console.log('📡 WebSocket закрыт')
            resetConnection()
        }

    } catch (error) {
        console.error('❌ Ошибка подключения:', error)
        alert(`Ошибка: ${error.message}`)
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

    // Перезапускаем камеру через секунду
    setTimeout(() => {
        if (!isConnected.value) {
            startCamera()
        }
    }, 1000)
}

const startConnectionTimer = () => {
    if (connectionTimer) clearInterval(connectionTimer)

    connectionTime.value = 0
    connectionTimer = setInterval(() => {
        connectionTime.value++
    }, 1000)
}

const toggleScannerCamera = async () => {
    if (isScannerActive.value) {
        stopScannerCamera()
    } else {
        await startScannerCamera()
    }
}

const startScannerCamera = async () => {
    try {
        const constraints = {
            video: {
                facingMode: { ideal: 'environment' },
                width: { ideal: 640 },
                height: { ideal: 640 }
            }
        }

        scannerCameraStream = await navigator.mediaDevices.getUserMedia(constraints)

        if (scannerVideoElement.value) {
            scannerVideoElement.value.srcObject = scannerCameraStream
            await scannerVideoElement.value.play()
            isScannerActive.value = true
            console.log('📷 Камера сканирования запущена')
        }

        // Запускаем тестовое сканирование каждые 3 секунды
        startProductScanning()

    } catch (error) {
        console.error('❌ Ошибка камеры:', error)
        alert(`Ошибка камеры: ${error.message}`)
    }
}

const stopScannerCamera = () => {
    if (scannerCameraStream) {
        scannerCameraStream.getTracks().forEach(track => track.stop())
        scannerCameraStream = null
    }
    if (scannerVideoElement.value) {
        scannerVideoElement.value.srcObject = null
    }
    isScannerActive.value = false
}

const startProductScanning = () => {
    // Тестовое сканирование каждые 3 секунды
    const productScanInterval = setInterval(() => {
        if (!isScannerActive.value) {
            clearInterval(productScanInterval)
            return
        }

        // 30% шанс на тестовое сканирование
        if (Math.random() < 0.3) {
            emulateQrScan()
        }
    }, 3000)
}

const testScan = () => {
    emulateQrScan()
}

const emulateQrScan = () => {
    const mockCodes = [
        'PROD-12345',
        'ITEM-67890',
        'SKU-98765',
        'CODE-54321',
        'ID-13579'
    ]

    const randomCode = mockCodes[Math.floor(Math.random() * mockCodes.length)]
    const timestamp = new Date()

    // Отправляем на компьютер через WebSocket
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        const message = {
            type: 'scan',
            qr_content: randomCode,
            timestamp: timestamp.toISOString()
        }

        try {
            wsConnection.send(JSON.stringify(message))

            scans.value.unshift({
                content: randomCode,
                timestamp: timestamp,
                sent: true
            })

            playScanBeep()

            console.log(`📤 Отправлен код: ${randomCode}`)

        } catch (error) {
            console.error('❌ Ошибка отправки:', error)
            scans.value.unshift({
                content: randomCode,
                timestamp: timestamp,
                sent: false
            })
        }
    } else {
        console.warn('⚠️ WebSocket не подключен')
        scans.value.unshift({
            content: randomCode,
            timestamp: timestamp,
            sent: false
        })
    }

    // Ограничиваем историю
    if (scans.value.length > 10) {
        scans.value = scans.value.slice(0, 10)
    }
}

const disconnect = () => {
    if (wsConnection) {
        wsConnection.close(1000, 'Пользователь отключился')
    }
    disconnectWebSocket()
    stopScannerCamera()
    resetConnection()
}

const disconnectWebSocket = () => {
    if (wsConnection) {
        wsConnection.close()
        wsConnection = null
    }
    isConnected.value = false
    currentSessionId.value = ''
    scans.value = []
}

const playSuccessBeep = () => {
    playBeep(800, 0.2)
}

const playScanBeep = () => {
    playBeep(1200, 0.1)
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
.phone-scanner-view {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-height: 100vh;
    padding: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.header {
    text-align: center;
    margin-bottom: 1rem;
}

.header h1 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.header p {
    opacity: 0.9;
}

.connect-section,
.scanner-section {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.connect-card {
    text-align: center;
}

.connect-card h3 {
    margin-bottom: 0.5rem;
    font-size: 1.3rem;
}

.connect-card p {
    margin-bottom: 1.5rem;
    opacity: 0.9;
}

/* Квадратные контейнеры для камеры */
.camera-preview,
.scanner-preview {
    position: relative;
    margin: 1rem 0;
    border-radius: 12px;
    overflow: hidden;
    background: black;
    width: 100%;
    height: 0;
    padding-bottom: 100%;
    /* Это делает контейнер квадратным */
}

.camera-video,
.scanner-video {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.scan-overlay {
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

.scan-frame {
    width: 70%;
    height: 70%;
    border: 3px solid rgba(40, 167, 69, 0.8);
    border-radius: 12px;
    position: relative;
    box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.7);
}

/* Уголки рамки */
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

/* Анимированная линия сканирования */
.scan-line {
    position: absolute;
    top: 15%;
    left: 50%;
    transform: translateX(-50%);
    width: 80%;
    height: 3px;
    background: linear-gradient(90deg, transparent, #28a745, transparent);
    animation: scan 2s linear infinite;
}

@keyframes scan {
    0% {
        top: 15%;
    }

    50% {
        top: 85%;
    }

    100% {
        top: 15%;
    }
}

.connection-status {
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

.status-error,
.status-scanning,
.status-waiting {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-weight: 500;
    text-align: center;
}

.status-error {
    color: #ff6b6b;
}

.status-waiting small {
    font-size: 0.8rem;
    opacity: 0.8;
    margin-top: 0.5rem;
}

.manual-connect {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.manual-input {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.manual-input input {
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

.hint {
    font-size: 0.8rem;
    opacity: 0.7;
    margin-top: 0.5rem;
}

/* Остальные стили остаются без изменений */
.connection-info {
    margin-bottom: 1.5rem;
}

.info-card {
    background: rgba(255, 255, 255, 0.1);
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
}

.info-card h3 {
    margin-bottom: 0.5rem;
    color: #28a745;
}

.session-info {
    margin: 0.5rem 0;
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    font-family: monospace;
    word-break: break-all;
}

.connection-stats {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 0.5rem;
    font-size: 0.9rem;
    opacity: 0.9;
}

.camera-section {
    margin-bottom: 1.5rem;
}

.camera-controls {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

.camera-toggle-btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
}

.scanner-placeholder {
    text-align: center;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    border: 2px dashed rgba(255, 255, 255, 0.2);
    margin: 1rem 0;
}

.placeholder-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-primary:hover {
    background: #0056b3;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-secondary:hover {
    background: #5a6268;
}

.btn-success {
    background: #28a745;
    color: white;
}

.btn-success:hover {
    background: #218838;
}

.btn-danger {
    background: #dc3545;
    color: white;
}

.btn-danger:hover {
    background: #c82333;
}

.btn-info {
    background: #17a2b8;
    color: white;
}

.btn-info:hover {
    background: #138496;
}

.btn-small {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
}

.scans-log {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 1rem;
}

.scans-log h4 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
}

.empty-scans {
    text-align: center;
    padding: 2rem;
    opacity: 0.7;
}

.scans-list {
    max-height: 200px;
    overflow-y: auto;
}

.scan-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    gap: 1rem;
}

.scan-item:last-child {
    border-bottom: none;
}

.scan-time {
    min-width: 85px;
    font-size: 0.9rem;
    opacity: 0.8;
}

.scan-content {
    flex: 1;
    font-family: monospace;
    word-break: break-all;
}

.scan-status {
    min-width: 20px;
    text-align: center;
    font-weight: bold;
    font-size: 1.2rem;
}

.status-sent {
    color: #28a745;
}

.status-error {
    color: #dc3545;
}

.status-bar {
    display: flex;
    justify-content: space-between;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 0.75rem;
    margin-top: auto;
    backdrop-filter: blur(10px);
}

.status-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-icon {
    font-size: 1rem;
}

.status-text {
    font-size: 0.9rem;
    opacity: 0.9;
}

@media (max-width: 768px) {
    .phone-scanner-view {
        padding: 0.5rem;
    }

    .camera-controls {
        flex-direction: column;
        align-items: stretch;
    }

    .status-bar {
        flex-direction: column;
        gap: 0.5rem;
    }

    .manual-input {
        flex-direction: column;
    }
}
</style>