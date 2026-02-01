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
                        <div class="scan-frame"></div>
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
                    </div>
                </div>

                <div class="manual-connect">
                    <p>Или введите ID подключения вручную:</p>
                    <div class="manual-input">
                        <input v-model="manualSessionId" placeholder="ID подключения" />
                        <button @click="connectManually" class="btn btn-primary">
                            Подключиться
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <div v-else class="scanner-section">
            <div class="connection-info">
                <div class="info-card">
                    <h3>✅ Подключено к компьютеру</h3>
                    <p>Теперь сканируйте QR-коды товаров</p>
                    <div class="session-info">
                        <strong>Сессия:</strong> {{ currentSessionId }}
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
                        <div class="scan-frame"></div>
                    </div>
                </div>
            </div>

            <div class="scans-log">
                <h4>История сканирований:</h4>
                <div v-if="scans.length === 0" class="empty-scans">
                    <p>Сканируйте QR-коды товаров, чтобы отправить их на печать</p>
                </div>
                <div v-else class="scans-list">
                    <div v-for="(scan, index) in scans" :key="index" class="scan-item">
                        <span class="scan-time">{{ formatTime(scan.timestamp) }}</span>
                        <span class="scan-content">{{ truncateText(scan.content, 25) }}</span>
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
                <span class="status-text">Сканов: {{ scans.length }}</span>
            </div>
            <div class="status-item">
                <span class="status-icon">📱</span>
                <span class="status-text">Телефон как сканер</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const videoElement = ref(null)
const scannerVideoElement = ref(null)
const isConnected = ref(false)
const isScanning = ref(false)
const isScannerActive = ref(false)
const cameraError = ref('')
const manualSessionId = ref('')
const currentSessionId = ref('')
const scans = ref([])

let connectCameraStream = null
let scannerCameraStream = null
let wsConnection = null
let scanInterval = null

onMounted(() => {
    startCamera()
})

onUnmounted(() => {
    stopCamera()
    stopScannerCamera()
    disconnectWebSocket()
    if (scanInterval) clearInterval(scanInterval)
})

const startCamera = async () => {
    try {
        cameraError.value = ''

        // Запрашиваем разрешение на использование камеры
        const constraints = {
            video: {
                facingMode: { ideal: 'environment' }, // Используем заднюю камеру
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        }

        // Прямой запрос доступа к камере
        connectCameraStream = await navigator.mediaDevices.getUserMedia(constraints)

        if (videoElement.value) {
            videoElement.value.srcObject = connectCameraStream
            videoElement.value.play().catch(e => console.log('Play error:', e))

            // Запускаем сканирование QR-кода подключения
            startQrScanning()
        }

    } catch (error) {
        console.error('Camera error:', error)

        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            cameraError.value = 'Доступ к камере запрещен. Разрешите доступ к камере в настройках браузера.'
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            cameraError.value = 'Камера не найдена'
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            cameraError.value = 'Камера уже используется другим приложением'
        } else if (error.name === 'OverconstrainedError') {
            cameraError.value = 'Невозможно использовать камеру с требуемыми параметрами'
        } else if (error.name === 'SecurityError') {
            cameraError.value = 'Доступ к камере заблокирован из соображений безопасности. Используйте HTTPS'
        } else {
            cameraError.value = `Ошибка камеры: ${error.message}`
        }
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
    // Эмуляция сканирования QR-кода
    // В реальности здесь должна быть библиотека для распознавания QR
    scanInterval = setInterval(() => {
        if (!videoElement.value || !connectCameraStream) return

        // Для демонстрации эмулируем сканирование при вводе ID
        if (manualSessionId.value) {
            connectToSession(manualSessionId.value)
            manualSessionId.value = ''
        }
    }, 1000)
}

const connectManually = () => {
    if (manualSessionId.value.trim()) {
        connectToSession(manualSessionId.value.trim())
    }
}

const connectToSession = async (sessionId) => {
    try {
        if (!sessionId.startsWith('rs_')) {
            alert('Неверный формат ID сессии. Должен начинаться с rs_')
            return
        }

        currentSessionId.value = sessionId

        // Подключаемся к WebSocket как клиент
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.hostname
        const port = window.location.port ? `:${window.location.port}` : ''
        const wsUrl = `${protocol}//${host}${port}/ws/remote-scanner/${sessionId}/client`

        wsConnection = new WebSocket(wsUrl)

        wsConnection.onopen = () => {
            console.log('Connected to computer as client')
            isConnected.value = true
            stopCamera()
            playBeep()
            alert('Подключено к компьютеру! Теперь сканируйте QR-коды товаров.')
        }

        wsConnection.onmessage = (event) => {
            const message = JSON.parse(event.data)
            console.log('Message from computer:', message)
        }

        wsConnection.onerror = (error) => {
            console.error('WebSocket error:', error)
            alert('Ошибка подключения к компьютеру')
            isConnected.value = false
        }

        wsConnection.onclose = () => {
            console.log('Disconnected from computer')
            isConnected.value = false
            currentSessionId.value = ''
            startCamera()
        }

    } catch (error) {
        console.error('Connection error:', error)
        alert(`Ошибка подключения: ${error.message}`)
    }
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
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        }

        scannerCameraStream = await navigator.mediaDevices.getUserMedia(constraints)

        if (scannerVideoElement.value) {
            scannerVideoElement.value.srcObject = scannerCameraStream
            scannerVideoElement.value.play().catch(e => console.log('Play error:', e))
            isScannerActive.value = true
        }

        // Запускаем эмуляцию сканирования товаров
        startProductScanning()

    } catch (error) {
        console.error('Scanner camera error:', error)
        alert(`Ошибка камеры сканера: ${error.message}`)
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
    // Эмуляция сканирования QR-кодов товаров
    const productScanInterval = setInterval(() => {
        if (!isScannerActive.value) {
            clearInterval(productScanInterval)
            return
        }

        // Эмулируем случайное сканирование
        if (Math.random() > 0.7) {
            emulateQrScan()
        }
    }, 2000)
}

const testScan = () => {
    emulateQrScan()
}

const emulateQrScan = () => {
    const mockCodes = [
        'PRODUCT-12345-ABC',
        'ITEM-67890-XYZ',
        'SKU-98765-QWE',
        'CODE-54321-RTY',
        'ID-13579-UIO'
    ]

    const randomCode = mockCodes[Math.floor(Math.random() * mockCodes.length)]
    const timestamp = new Date()

    // Отправляем на компьютер через WebSocket
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        const message = {
            type: 'scan',
            qr_content: randomCode,
            timestamp: timestamp.toISOString(),
            device: 'phone'
        }

        try {
            wsConnection.send(JSON.stringify(message))

            scans.value.unshift({
                content: randomCode,
                timestamp: timestamp,
                sent: true
            })

            playBeep()

        } catch (error) {
            scans.value.unshift({
                content: randomCode,
                timestamp: timestamp,
                sent: false
            })
        }
    } else {
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
    disconnectWebSocket()
    stopScannerCamera()
    startCamera()
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

const playBeep = () => {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()

        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)

        oscillator.frequency.value = 1000
        oscillator.type = 'sine'

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1)

        oscillator.start(audioContext.currentTime)
        oscillator.stop(audioContext.currentTime + 0.1)
    } catch (e) {
        // Audio not supported
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
        minute: '2-digit'
    })
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

.camera-preview,
.scanner-preview {
    position: relative;
    margin: 1rem 0;
    border-radius: 8px;
    overflow: hidden;
    background: black;
    min-height: 250px;
}

.camera-video,
.scanner-video {
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
}

.scan-frame {
    width: 70%;
    height: 70%;
    border: 3px solid #28a745;
    border-radius: 8px;
    box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.5);
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
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-weight: 500;
}

.status-error {
    color: #ff6b6b;
    flex-direction: column;
    text-align: center;
}

.manual-connect {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.manual-input {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.manual-input input {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    font-size: 1rem;
}

.manual-input input::placeholder {
    color: rgba(255, 255, 255, 0.6);
}

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
    min-width: 70px;
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