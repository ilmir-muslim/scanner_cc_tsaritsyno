<template>
    <div class="phone-scanner-view">
        <div class="header">
            <h1>📱 Камера телефона как сканер</h1>
            <p>Сканируйте QR-коды и отправляйте их на печать на компьютере</p>
        </div>

        <!-- Состояние: запрос разрешения камеры -->
        <div v-if="cameraPermission === 'prompt'" class="permission-section">
            <div class="permission-card">
                <div class="permission-icon">📷</div>
                <h3>Требуется доступ к камере</h3>
                <p>Для работы сканера необходимо разрешить доступ к камере вашего устройства</p>
                
                <button @click="requestCameraPermission" class="btn btn-primary btn-lg">
                    Разрешить доступ к камере
                </button>
                
                <div class="permission-tip">
                    <p><strong>Если доступ не запрашивается автоматически:</strong></p>
                    <ol>
                        <li>Проверьте настройки браузера</li>
                        <li>Разрешите доступ к камере вручную</li>
                        <li>Обновите страницу</li>
                    </ol>
                </div>
            </div>
        </div>

        <!-- Состояние: доступ к камере запрещен -->
        <div v-else-if="cameraPermission === 'denied'" class="permission-section">
            <div class="permission-card error">
                <div class="permission-icon">❌</div>
                <h3>Доступ к камере запрещен</h3>
                <p>Невозможно использовать камеру. Разрешите доступ к камере в настройках браузера.</p>
                
                <div class="error-steps">
                    <h4>Как разрешить доступ:</h4>
                    <ol>
                        <li>Откройте настройки браузера</li>
                        <li>Найдите "Настройки сайта" или "Разрешения"</li>
                        <li>Найдите этот сайт в списке</li>
                        <li>Разрешите доступ к камере</li>
                        <li>Обновите страницу</li>
                    </ol>
                </div>
                
                <button @click="checkCameraPermission" class="btn btn-secondary">
                    Проверить снова
                </button>
            </div>
        </div>

        <!-- Состояние: доступ к камере разрешен, но не подключено -->
        <div v-else-if="!isConnected && cameraPermission === 'granted'" class="connect-section">
            <div class="connect-card">
                <h3>Подключение к компьютеру</h3>
                <p>Отсканируйте QR-код с компьютера для подключения</p>
                
                <div class="camera-preview">
                    <video ref="videoElement" autoplay playsinline class="camera-video"></video>
                    <div class="scan-overlay">
                        <div class="scan-frame"></div>
                        <div class="scan-text">Наведите на QR-код подключения</div>
                    </div>
                </div>
                
                <div class="connection-status">
                    <div v-if="isScanning" class="status-scanning">
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
                        <input v-model="manualSessionId" placeholder="rs_123456789_abc123" />
                        <button @click="connectManually" class="btn btn-primary" :disabled="!manualSessionId.trim()">
                            Подключиться
                        </button>
                    </div>
                </div>
                
                <div class="camera-info">
                    <p><small>Камера: {{ cameraInfo.device || 'Не выбрана' }}</small></p>
                    <button @click="switchCamera" class="btn btn-small">
                        🔄 Сменить камеру
                    </button>
                </div>
            </div>
        </div>

        <!-- Состояние: подключено к компьютеру -->
        <div v-else-if="isConnected" class="scanner-section">
            <div class="connection-info">
                <div class="info-card">
                    <h3>✅ Подключено к компьютеру</h3>
                    <p>Теперь сканируйте QR-коды товаров</p>
                    <div class="session-info">
                        <strong>Сессия:</strong> <code>{{ currentSessionId }}</code>
                    </div>
                    <div class="connection-stats">
                        <span>Отправлено: {{ sentScansCount }} сканов</span>
                        <span>Ошибок: {{ errorScansCount }}</span>
                    </div>
                </div>
            </div>

            <div class="camera-section">
                <div class="camera-controls">
                    <button @click="toggleScannerCamera" 
                            :class="['camera-toggle-btn', isScannerActive ? 'btn-danger' : 'btn-success']">
                        {{ isScannerActive ? '⏸️ Остановить сканирование' : '▶️ Начать сканирование' }}
                    </button>
                    
                    <button @click="testScan" class="btn btn-info" :disabled="!isScannerActive">
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
                        <div class="scan-text">Наведите на QR-код товара</div>
                    </div>
                    
                    <div class="scanner-status">
                        <span class="scanner-icon">📸</span>
                        <span class="scanner-text">Сканер активен</span>
                        <span class="scanner-count">Сканов: {{ scans.length }}</span>
                    </div>
                </div>
                <div v-else class="scanner-inactive">
                    <div class="inactive-icon">⏸️</div>
                    <p>Сканирование остановлено</p>
                    <p>Нажмите "Начать сканирование" чтобы продолжить</p>
                </div>
            </div>

            <div class="scans-log">
                <div class="log-header">
                    <h4>История сканирований:</h4>
                    <button @click="clearScans" class="btn btn-small" :disabled="scans.length === 0">
                        🗑️ Очистить
                    </button>
                </div>
                
                <div v-if="scans.length === 0" class="empty-scans">
                    <div class="empty-icon">📭</div>
                    <p>Сканируйте QR-коды товаров, чтобы отправить их на печать</p>
                    <p><small>История сканирований появится здесь</small></p>
                </div>
                <div v-else class="scans-list">
                    <div v-for="(scan, index) in scans" :key="index" class="scan-item" :class="{ 'scan-error': !scan.sent }">
                        <span class="scan-index">#{{ scans.length - index }}</span>
                        <span class="scan-time">{{ formatTime(scan.timestamp) }}</span>
                        <span class="scan-content" :title="scan.content">{{ truncateText(scan.content, 25) }}</span>
                        <span :class="['scan-status', scan.sent ? 'status-sent' : 'status-error']">
                            {{ scan.sent ? '✓ Отправлено' : '✗ Ошибка' }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Статус бар -->
        <div class="status-bar">
            <div class="status-item">
                <span class="status-icon">{{ isConnected ? '📱✅' : '📱❌' }}</span>
                <span class="status-text">{{ isConnected ? 'Подключено' : 'Не подключено' }}</span>
            </div>
            <div class="status-item">
                <span class="status-icon">{{ isScannerActive ? '📸' : '📷' }}</span>
                <span class="status-text">{{ isScannerActive ? 'Сканирует' : 'Камера' }}</span>
            </div>
            <div class="status-item">
                <span class="status-icon">🔋</span>
                <span class="status-text">{{ batteryLevel }}%</span>
            </div>
        </div>
        
        <!-- Уведомления -->
        <div v-if="notification.show" :class="['notification', notification.type]">
            {{ notification.message }}
            <button @click="notification.show = false" class="notification-close">×</button>
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
const cameraPermission = ref('prompt') // 'prompt', 'granted', 'denied'
const manualSessionId = ref('')
const currentSessionId = ref('')
const scans = ref([])
const cameraInfo = ref({ device: null })
const batteryLevel = ref(100)

const notification = ref({
    show: false,
    message: '',
    type: 'info' // 'info', 'success', 'error'
})

let connectCameraStream = null
let scannerCameraStream = null
let wsConnection = null
let scanInterval = null
let cameraDevices = []

onMounted(async () => {
    checkCameraPermission()
    checkBatteryLevel()
})

onUnmounted(() => {
    stopConnectCamera()
    stopScannerCamera()
    disconnectWebSocket()
    if (scanInterval) clearInterval(scanInterval)
})

const checkCameraPermission = async () => {
    try {
        const permission = await navigator.permissions.query({ name: 'camera' })
        cameraPermission.value = permission.state
        
        permission.onchange = () => {
            cameraPermission.value = permission.state
            if (permission.state === 'granted') {
                startConnectCamera()
            } else {
                stopConnectCamera()
                stopScannerCamera()
            }
        }
        
        if (permission.state === 'granted') {
            startConnectCamera()
        }
    } catch (error) {
        console.error('Permission check error:', error)
        // Fallback для старых браузеров
        cameraPermission.value = 'prompt'
    }
}

const requestCameraPermission = async () => {
    try {
        // Запрашиваем разрешение через getUserMedia
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
        })
        
        // Останавливаем стрим, так как мы только проверяли разрешение
        stream.getTracks().forEach(track => track.stop())
        
        cameraPermission.value = 'granted'
        showNotification('Доступ к камере разрешен', 'success')
        startConnectCamera()
        
    } catch (error) {
        console.error('Camera permission error:', error)
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            cameraPermission.value = 'denied'
            showNotification('Доступ к камере запрещен', 'error')
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            showNotification('Камера не найдена', 'error')
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            showNotification('Ошибка доступа к камере', 'error')
        } else {
            showNotification('Неизвестная ошибка камеры', 'error')
        }
    }
}

const getCameraDevices = async () => {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        cameraDevices = devices.filter(device => device.kind === 'videoinput')
        
        if (cameraDevices.length > 0) {
            cameraInfo.value.device = cameraDevices[0].label || 'Основная камера'
        }
        
        return cameraDevices
    } catch (error) {
        console.error('Error enumerating devices:', error)
        return []
    }
}

const switchCamera = async () => {
    if (cameraDevices.length < 2) {
        showNotification('Только одна камера доступна', 'info')
        return
    }
    
    stopConnectCamera()
    await startConnectCamera(true)
}

const startConnectCamera = async (switchCamera = false) => {
    try {
        await getCameraDevices()
        
        const constraints = {
            video: {
                facingMode: { ideal: 'environment' },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        }

        connectCameraStream = await navigator.mediaDevices.getUserMedia(constraints)

        if (videoElement.value) {
            videoElement.value.srcObject = connectCameraStream
            videoElement.value.play()
        }
        
        // Обновляем информацию о камере
        const tracks = connectCameraStream.getVideoTracks()
        if (tracks.length > 0) {
            const settings = tracks[0].getSettings()
            cameraInfo.value = {
                device: tracks[0].label || 'Камера',
                resolution: `${settings.width || 0}x${settings.height || 0}`,
                frameRate: settings.frameRate || 0
            }
        }
        
        // Запускаем сканирование QR-кода подключения
        startQrScanning()
        
    } catch (error) {
        console.error('Error starting camera:', error)
        
        if (error.name === 'NotAllowedError') {
            cameraPermission.value = 'denied'
            showNotification('Разрешите доступ к камере в настройках', 'error')
        } else {
            showNotification(`Ошибка камеры: ${error.message}`, 'error')
        }
    }
}

const stopConnectCamera = () => {
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
    scanInterval = setInterval(async () => {
        if (!videoElement.value || !connectCameraStream || !isScanning.value) return
        
        try {
            // Эмуляция сканирования QR-кода
            // В реальном проекте здесь должна быть логика распознавания QR-кодов
            if (manualSessionId.value) {
                await connectToSession(manualSessionId.value)
                manualSessionId.value = ''
            }
            
        } catch (error) {
            console.error('QR scan error:', error)
        }
    }, 1000)
}

const connectManually = () => {
    if (manualSessionId.value.trim()) {
        isScanning.value = true
        connectToSession(manualSessionId.value.trim())
    }
}

const connectToSession = async (sessionId) => {
    try {
        if (!sessionId.startsWith('rs_')) {
            showNotification('Неверный формат ID сессии', 'error')
            return
        }
        
        currentSessionId.value = sessionId
        isScanning.value = true
        
        // Подключаемся к WebSocket как клиент
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        const wsUrl = `${protocol}//${host}/ws/remote-scanner/${sessionId}/client`
        
        wsConnection = new WebSocket(wsUrl)
        
        wsConnection.onopen = () => {
            console.log('Connected to computer as client')
            isConnected.value = true
            isScanning.value = false
            stopConnectCamera()
            showNotification('Подключено к компьютеру', 'success')
            playBeep()
        }
        
        wsConnection.onmessage = (event) => {
            const message = JSON.parse(event.data)
            console.log('Message from computer:', message)
            
            if (message.type === 'status') {
                showNotification(`Статус: ${message.status}`, 'info')
            }
        }
        
        wsConnection.onerror = (error) => {
            console.error('WebSocket error:', error)
            showNotification('Ошибка подключения к компьютеру', 'error')
            isConnected.value = false
        }
        
        wsConnection.onclose = () => {
            console.log('Disconnected from computer')
            isConnected.value = false
            currentSessionId.value = ''
            showNotification('Отключено от компьютера', 'info')
            startConnectCamera()
        }
        
    } catch (error) {
        console.error('Connection error:', error)
        isConnected.value = false
        isScanning.value = false
        showNotification(`Ошибка: ${error.message}`, 'error')
    }
}

const toggleScannerCamera = async () => {
    if (isScannerActive.value) {
        stopScannerCamera()
        showNotification('Сканирование остановлено', 'info')
    } else {
        await startScannerCamera()
        showNotification('Сканирование начато', 'success')
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
            scannerVideoElement.value.play()
            isScannerActive.value = true
        }
        
        // Запускаем сканирование QR-кодов товаров
        startProductScanning()
        
    } catch (error) {
        console.error('Error starting scanner camera:', error)
        showNotification(`Ошибка камеры: ${error.message}`, 'error')
        isScannerActive.value = false
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
    // В реальном проекте здесь должна быть библиотека для распознавания QR-кодов
    const productScanInterval = setInterval(() => {
        if (!isScannerActive.value) {
            clearInterval(productScanInterval)
            return
        }
        
        // Для демонстрации эмулируем сканирование случайного QR-кода каждые 3 секунды
        if (Math.random() > 0.5) {
            emulateQrScan()
        }
    }, 3000)
}

const testScan = () => {
    if (!isScannerActive.value) {
        showNotification('Сначала запустите сканирование', 'error')
        return
    }
    
    emulateQrScan()
}

const emulateQrScan = () => {
    const mockCodes = [
        'PRODUCT-12345-ABC',
        'ITEM-67890-XYZ',
        'SKU-98765-QWE',
        'CODE-54321-RTY',
        'ID-13579-UIO',
        'LABEL-24680-PLM',
        'TAG-36912-KNJ',
        'SCAN-48263-MVB'
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
            
            showNotification(`Отсканировано: ${truncateText(randomCode, 20)}`, 'success')
            playBeep()
            
        } catch (error) {
            scans.value.unshift({
                content: randomCode,
                timestamp: timestamp,
                sent: false,
                error: error.message
            })
            
            showNotification('Ошибка отправки на компьютер', 'error')
        }
    } else {
        scans.value.unshift({
            content: randomCode,
            timestamp: timestamp,
            sent: false,
            error: 'Нет подключения'
        })
        
        showNotification('Нет подключения к компьютеру', 'error')
    }
    
    // Ограничиваем историю 20 записями
    if (scans.value.length > 20) {
        scans.value = scans.value.slice(0, 20)
    }
}

const sentScansCount = computed(() => {
    return scans.value.filter(scan => scan.sent).length
})

const errorScansCount = computed(() => {
    return scans.value.filter(scan => !scan.sent).length
})

const disconnect = () => {
    disconnectWebSocket()
    stopScannerCamera()
    startConnectCamera()
    showNotification('Отключено от компьютера', 'info')
}

const disconnectWebSocket = () => {
    if (wsConnection) {
        wsConnection.close()
        wsConnection = null
    }
    isConnected.value = false
    currentSessionId.value = ''
}

const clearScans = () => {
    scans.value = []
    showNotification('История очищена', 'info')
}

const showNotification = (message, type = 'info') => {
    notification.value = {
        show: true,
        message,
        type
    }
    
    setTimeout(() => {
        notification.value.show = false
    }, 3000)
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

const checkBatteryLevel = () => {
    if ('getBattery' in navigator) {
        navigator.getBattery().then(battery => {
            batteryLevel.value = Math.round(battery.level * 100)
            
            battery.addEventListener('levelchange', () => {
                batteryLevel.value = Math.round(battery.level * 100)
            })
        })
    } else if ('battery' in navigator) {
        // Для старых браузеров
        batteryLevel.value = navigator.battery ? Math.round(navigator.battery.level * 100) : 100
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

/* Секции разрешений */
.permission-section, .connect-section, .scanner-section {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.permission-card {
    text-align: center;
    padding: 2rem;
}

.permission-card.error {
    background: rgba(220, 53, 69, 0.1);
    border-color: rgba(220, 53, 69, 0.3);
}

.permission-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.8;
}

.permission-card h3 {
    margin-bottom: 1rem;
    font-size: 1.3rem;
}

.permission-card p {
    margin-bottom: 1.5rem;
    opacity: 0.9;
}

.permission-tip, .error-steps {
    margin-top: 1.5rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    text-align: left;
}

.permission-tip ol, .error-steps ol {
    padding-left: 1.5rem;
    margin: 0.5rem 0;
}

.permission-tip li, .error-steps li {
    margin-bottom: 0.5rem;
}

/* Основной интерфейс подключения */
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

.camera-preview, .scanner-preview {
    position: relative;
    margin: 1rem 0;
    border-radius: 8px;
    overflow: hidden;
    background: black;
    min-height: 250px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.camera-video, .scanner-video {
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
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.scan-frame {
    width: 70%;
    height: 50%;
    border: 3px solid #28a745;
    border-radius: 8px;
    box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.5);
}

.scan-text {
    margin-top: 1rem;
    color: white;
    font-weight: 500;
    background: rgba(0, 0, 0, 0.7);
    padding: 0.5rem 1rem;
    border-radius: 20px;
}

.connection-status {
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

.status-scanning, .status-waiting {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-weight: 500;
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

.camera-info {
    margin-top: 1rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Интерфейс сканирования */
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
    opacity: 0.8;
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

.scanner-status {
    position: absolute;
    bottom: 10px;
    left: 10px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
}

.scanner-inactive {
    text-align: center;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
}

.inactive-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

/* История сканирований */
.scans-log {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 1rem;
}

.log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.scans-log h4 {
    margin: 0;
    font-size: 1.1rem;
}

.empty-scans {
    text-align: center;
    padding: 2rem;
    opacity: 0.7;
}

.empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.scans-list {
    max-height: 300px;
    overflow-y: auto;
}

.scan-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    gap: 1rem;
    transition: background 0.2s;
}

.scan-item:hover {
    background: rgba(255, 255, 255, 0.05);
}

.scan-item:last-child {
    border-bottom: none;
}

.scan-item.scan-error {
    background: rgba(220, 53, 69, 0.1);
}

.scan-index {
    min-width: 30px;
    opacity: 0.6;
    font-size: 0.9rem;
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
    cursor: help;
}

.scan-status {
    min-width: 80px;
    text-align: center;
    font-weight: 500;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
}

.status-sent {
    background: rgba(40, 167, 69, 0.2);
    color: #28a745;
}

.status-error {
    background: rgba(220, 53, 69, 0.2);
    color: #dc3545;
}

/* Статус бар */
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

/* Уведомления */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    animation: slideIn 0.3s ease-out;
    max-width: 300px;
}

.notification.info {
    background: rgba(23, 162, 184, 0.9);
}

.notification.success {
    background: rgba(40, 167, 69, 0.9);
}

.notification.error {
    background: rgba(220, 53, 69, 0.9);
}

.notification-close {
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    line-height: 1;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Кнопки */
.btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #0056b3;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-secondary:hover:not(:disabled) {
    background: #5a6268;
}

.btn-success {
    background: #28a745;
    color: white;
}

.btn-success:hover:not(:disabled) {
    background: #218838;
}

.btn-danger {
    background: #dc3545;
    color: white;
}

.btn-danger:hover:not(:disabled) {
    background: #c82333;
}

.btn-info {
    background: #17a2b8;
    color: white;
}

.btn-info:hover:not(:disabled) {
    background: #138496;
}

.btn-small {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
}

.btn-lg {
    padding: 1rem 2rem;
    font-size: 1.1rem;
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
    
    .scan-item {
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .scan-time, .scan-index {
        min-width: auto;
    }
    
    .notification {
        left: 20px;
        right: 20px;
        max-width: none;
    }
}
</style>