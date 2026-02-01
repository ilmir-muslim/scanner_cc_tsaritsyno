<template>
    <div class="phone-scanner-view">
        <div class="header">
            <h1>📱 Камера телефона как сканер</h1>
            <p>Сканируйте QR-коды и отправляйте их на печать на компьютере</p>
        </div>

        <!-- Камера не включена -->
        <div v-if="!isCameraActive" class="camera-off-section">
            <div class="camera-off-card">
                <div class="camera-off-icon">📷</div>
                <h3>Камера не активна</h3>
                <p>Для работы сканера необходимо включить камеру</p>

                <button @click="activateCamera" class="btn btn-primary btn-lg">
                    Включить камеру
                </button>

                <div class="camera-tips">
                    <p><strong>Советы:</strong></p>
                    <ul>
                        <li>Разрешите доступ к камере в диалоге браузера</li>
                        <li>Убедитесь, что камера не используется другим приложением</li>
                        <li>Обновите страницу при проблемах</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Камера активна, не подключено -->
        <div v-else-if="!isConnected" class="connect-section">
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

                <div class="camera-controls">
                    <button @click="toggleCamera" class="btn btn-danger">
                        🔴 Выключить камеру
                    </button>
                    <button @click="switchCamera" class="btn btn-secondary">
                        🔄 Сменить камеру
                    </button>
                </div>

                <div class="connection-status">
                    <div class="status-waiting">
                        <span class="status-icon">🔍</span>
                        <span>Сканирование QR-кода подключения...</span>
                    </div>
                </div>

                <div class="manual-connect">
                    <p>Или введите ID подключения вручную:</p>
                    <div class="manual-input">
                        <input v-model="manualSessionId" placeholder="Введите ID подключения"
                            @keyup.enter="connectManually" />
                        <button @click="connectManually" class="btn btn-primary" :disabled="!manualSessionId.trim()">
                            Подключиться
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Подключено к компьютеру -->
        <div v-else class="scanner-section">
            <div class="connection-info">
                <div class="info-card">
                    <div class="info-header">
                        <h3>✅ Подключено к компьютеру</h3>
                        <button @click="disconnect" class="btn btn-small btn-danger">
                            ✖️ Отключиться
                        </button>
                    </div>
                    <p>Сканируйте QR-коды товаров</p>
                    <div class="session-info">
                        <strong>Сессия:</strong> <code>{{ currentSessionId }}</code>
                    </div>
                    <div class="connection-stats">
                        <span>📤 Отправлено: {{ sentScansCount }}</span>
                        <span>❌ Ошибок: {{ errorScansCount }}</span>
                    </div>
                </div>
            </div>

            <div class="camera-section">
                <div class="scanner-controls">
                    <button @click="toggleScanner"
                        :class="['scanner-toggle-btn', isScannerActive ? 'btn-danger' : 'btn-success']">
                        {{ isScannerActive ? '⏸️ Остановить сканирование' : '▶️ Начать сканирование' }}
                    </button>

                    <button @click="testScan" class="btn btn-info" :disabled="!isScannerActive">
                        🔍 Тестовое сканирование
                    </button>

                    <button @click="toggleCamera" class="btn btn-secondary">
                        📷 Управление камерой
                    </button>
                </div>

                <div v-if="isScannerActive" class="scanner-preview">
                    <video ref="scannerVideoElement" autoplay playsinline class="scanner-video"></video>
                    <div class="scan-overlay">
                        <div class="scan-frame"></div>
                        <div class="scan-text">Наведите на QR-код товара</div>
                        <div class="scan-counter">Сканов: {{ scans.length }}</div>
                    </div>

                    <div class="scanner-status">
                        <span class="scanner-icon">📸</span>
                        <span class="scanner-text active">Сканирует...</span>
                    </div>
                </div>

                <div v-else class="scanner-inactive">
                    <div class="inactive-icon">⏸️</div>
                    <h4>Сканирование остановлено</h4>
                    <p>Нажмите "Начать сканирование" чтобы продолжить</p>
                    <button @click="testScan" class="btn btn-info btn-small">
                        🔍 Протестировать без камеры
                    </button>
                </div>
            </div>

            <div class="scans-log">
                <div class="log-header">
                    <h4>📋 История сканирований</h4>
                    <div class="log-controls">
                        <button @click="clearScans" class="btn btn-small btn-danger" :disabled="scans.length === 0">
                            🗑️ Очистить
                        </button>
                        <button @click="toggleAutoScroll" class="btn btn-small"
                            :class="autoScroll ? 'btn-success' : 'btn-secondary'">
                            {{ autoScroll ? '🔒 Автопрокрутка: ВКЛ' : '🔓 Автопрокрутка: ВЫКЛ' }}
                        </button>
                    </div>
                </div>

                <div v-if="scans.length === 0" class="empty-scans">
                    <div class="empty-icon">📭</div>
                    <p>История сканирований пуста</p>
                    <p><small>Отсканируйте QR-коды, чтобы они появились здесь</small></p>
                </div>

                <div v-else class="scans-list" ref="scansList">
                    <div v-for="(scan, index) in scans" :key="index" class="scan-item"
                        :class="{ 'scan-error': !scan.sent }"
                        :title="scan.error ? `Ошибка: ${scan.error}` : 'Успешно отправлено'">
                        <span class="scan-index">#{{ scans.length - index }}</span>
                        <span class="scan-time">{{ formatTime(scan.timestamp) }}</span>
                        <span class="scan-content">{{ scan.content }}</span>
                        <span :class="['scan-status', scan.sent ? 'status-sent' : 'status-error']">
                            {{ scan.sent ? '✓' : '✗' }}
                        </span>
                    </div>
                </div>

                <div v-if="scans.length > 0" class="log-summary">
                    <span>Всего: {{ scans.length }} | Успешно: {{ sentScansCount }} | Ошибок:
                        {{ errorScansCount }}</span>
                </div>
            </div>
        </div>

        <!-- Статус бар -->
        <div class="status-bar">
            <div class="status-item" @click="toggleCamera" style="cursor: pointer;">
                <span class="status-icon">{{ isCameraActive ? '📹' : '📷' }}</span>
                <span class="status-text">{{ isCameraActive ? 'Камера: ВКЛ' : 'Камера: ВЫКЛ' }}</span>
            </div>

            <div class="status-item" @click="toggleScanner" style="cursor: pointer;">
                <span class="status-icon">{{ isScannerActive ? '🔍' : '⏸️' }}</span>
                <span class="status-text">{{ isScannerActive ? 'Сканирует' : 'Пауза' }}</span>
            </div>

            <div class="status-item">
                <span class="status-icon">📤</span>
                <span class="status-text">{{ sentScansCount }}</span>
            </div>
        </div>

        <!-- Уведомление -->
        <div v-if="notification.show" :class="['notification', notification.type]" @click="notification.show = false">
            <span class="notification-icon">
                {{ notification.type === 'success' ? '✅' :
                    notification.type === 'error' ? '❌' : 'ℹ️' }}
            </span>
            <span class="notification-message">{{ notification.message }}</span>
            <span class="notification-close">×</span>
        </div>

        <!-- Прогресс -->
        <div v-if="isProcessing" class="processing-overlay">
            <div class="processing-spinner"></div>
            <div class="processing-text">Обработка...</div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'

// Refs
const videoElement = ref(null)
const scannerVideoElement = ref(null)
const scansList = ref(null)

const isCameraActive = ref(false)
const isConnected = ref(false)
const isScannerActive = ref(false)
const isProcessing = ref(false)
const autoScroll = ref(true)

const manualSessionId = ref('')
const currentSessionId = ref('')
const scans = ref([])
const notification = ref({
    show: false,
    message: '',
    type: 'info'
})

// WebSocket и камера
let wsConnection = null
let cameraStream = null
let scannerStream = null
let scanInterval = null
let cameraDevices = []
let currentCameraIndex = 0

// Запрос доступа к камере
const activateCamera = async () => {
    if (isCameraActive.value) return

    isProcessing.value = true

    try {
        // Прямой запрос доступа к камере
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: 'environment' }, // Используем заднюю камеру
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 30 }
            },
            audio: false
        })

        cameraStream = stream

        if (videoElement.value) {
            videoElement.value.srcObject = stream
            videoElement.value.play().catch(e => console.log('Play error:', e))
        }

        isCameraActive.value = true
        showNotification('Камера включена', 'success')

        // Получаем список камер
        await getCameraDevices()

        // Запускаем сканирование QR-кода подключения
        startConnectionScanning()

    } catch (error) {
        console.error('Camera activation error:', error)

        let errorMessage = 'Не удалось включить камеру'

        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMessage = 'Доступ к камере запрещен. Разрешите доступ в настройках браузера.'
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            errorMessage = 'Камера не найдена'
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            errorMessage = 'Ошибка доступа к камере. Убедитесь, что она не используется другим приложением.'
        } else if (error.name === 'OverconstrainedError') {
            errorMessage = 'Требуемые параметры камеры недоступны'
        } else if (error.name === 'TypeError') {
            errorMessage = 'Некорректные параметры камеры'
        }

        showNotification(errorMessage, 'error')

    } finally {
        isProcessing.value = false
    }
}

// Выключение камеры
const toggleCamera = () => {
    if (isCameraActive.value) {
        stopCamera()
        showNotification('Камера выключена', 'info')
    } else {
        activateCamera()
    }
}

const stopCamera = () => {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop())
        cameraStream = null
    }

    if (videoElement.value) {
        videoElement.value.srcObject = null
    }

    if (scanInterval) {
        clearInterval(scanInterval)
        scanInterval = null
    }

    isCameraActive.value = false
    isScannerActive.value = false
}

// Смена камеры
const switchCamera = async () => {
    if (!cameraStream || cameraDevices.length < 2) {
        showNotification('Доступна только одна камера', 'info')
        return
    }

    isProcessing.value = true

    try {
        // Останавливаем текущую камеру
        cameraStream.getTracks().forEach(track => track.stop())

        // Переключаемся на следующую камеру
        currentCameraIndex = (currentCameraIndex + 1) % cameraDevices.length
        const deviceId = cameraDevices[currentCameraIndex].deviceId

        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                deviceId: { exact: deviceId },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        })

        cameraStream = stream

        if (videoElement.value) {
            videoElement.value.srcObject = stream
            videoElement.value.play().catch(e => console.log('Play error:', e))
        }

        showNotification('Камера изменена', 'success')

    } catch (error) {
        console.error('Camera switch error:', error)
        showNotification('Ошибка смены камеры', 'error')
    } finally {
        isProcessing.value = false
    }
}

// Получение списка камер
const getCameraDevices = async () => {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        cameraDevices = devices.filter(device => device.kind === 'videoinput')
        return cameraDevices
    } catch (error) {
        console.error('Error getting camera devices:', error)
        return []
    }
}

// Сканирование QR-кода для подключения
const startConnectionScanning = () => {
    if (scanInterval) clearInterval(scanInterval)

    scanInterval = setInterval(() => {
        if (!isCameraActive.value || isConnected.value) return

        // В реальном проекте здесь должен быть код распознавания QR-кода
        // Для демонстрации используем ручной ввод
        if (manualSessionId.value.trim()) {
            connectToSession(manualSessionId.value.trim())
        }
    }, 1000)
}

// Подключение к сессии
const connectManually = () => {
    if (manualSessionId.value.trim()) {
        connectToSession(manualSessionId.value.trim())
    }
}

const connectToSession = async (sessionId) => {
    if (isConnected.value) return

    isProcessing.value = true

    try {
        currentSessionId.value = sessionId

        // Подключаемся к WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        const wsUrl = `${protocol}//${host}/ws/remote-scanner/${sessionId}/client`

        wsConnection = new WebSocket(wsUrl)

        wsConnection.onopen = () => {
            console.log('WebSocket connected')
            isConnected.value = true
            manualSessionId.value = ''

            // Останавливаем сканирование подключения
            if (scanInterval) {
                clearInterval(scanInterval)
                scanInterval = null
            }

            showNotification('Подключено к компьютеру!', 'success')
            playBeep()
        }

        wsConnection.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data)
                console.log('WebSocket message:', message)

                if (message.type === 'status') {
                    showNotification(`Статус: ${message.status}`, 'info')
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error)
            }
        }

        wsConnection.onerror = (error) => {
            console.error('WebSocket error:', error)
            showNotification('Ошибка подключения', 'error')
        }

        wsConnection.onclose = () => {
            console.log('WebSocket closed')
            isConnected.value = false
            currentSessionId.value = ''
            wsConnection = null

            // Возвращаемся к сканированию подключения
            if (isCameraActive.value && !isConnected.value) {
                startConnectionScanning()
            }

            showNotification('Отключено от компьютера', 'info')
        }

        // Таймаут подключения
        setTimeout(() => {
            if (!isConnected.value && wsConnection) {
                wsConnection.close()
                showNotification('Таймаут подключения', 'error')
            }
        }, 10000)

    } catch (error) {
        console.error('Connection error:', error)
        showNotification(`Ошибка: ${error.message}`, 'error')
        isConnected.value = false
        currentSessionId.value = ''
    } finally {
        isProcessing.value = false
    }
}

// Управление сканированием товаров
const toggleScanner = () => {
    if (!isConnected.value) {
        showNotification('Сначала подключитесь к компьютеру', 'error')
        return
    }

    if (isScannerActive.value) {
        stopScanner()
        showNotification('Сканирование остановлено', 'info')
    } else {
        startScanner()
        showNotification('Сканирование начато', 'success')
    }
}

const startScanner = () => {
    if (!isConnected.value || isScannerActive.value) return

    isScannerActive.value = true

    // В реальном проекте здесь должна быть логика сканирования QR-кодов
    // Для демонстрации эмулируем сканирование
    const scannerInterval = setInterval(() => {
        if (!isScannerActive.value) {
            clearInterval(scannerInterval)
            return
        }

        // Эмуляция случайного сканирования
        if (Math.random() > 0.7) {
            emulateQrScan()
        }
    }, 2000)
}

const stopScanner = () => {
    isScannerActive.value = false
}

// Эмуляция сканирования QR-кода
const emulateQrScan = () => {
    if (!isConnected.value || !wsConnection || wsConnection.readyState !== WebSocket.OPEN) {
        showNotification('Нет подключения к компьютеру', 'error')
        return
    }

    const mockCodes = [
        'PRODUCT-12345-ABC-' + Date.now(),
        'ITEM-67890-XYZ-' + Math.random().toString(36).substr(2, 6),
        'SKU-98765-QWE-' + Date.now().toString(36),
        'CODE-54321-RTY-' + Math.floor(Math.random() * 10000),
        'ID-13579-UIO-' + new Date().getTime()
    ]

    const randomCode = mockCodes[Math.floor(Math.random() * mockCodes.length)]
    const timestamp = new Date()

    try {
        const message = {
            type: 'scan',
            qr_content: randomCode,
            timestamp: timestamp.toISOString(),
            device: 'phone',
            session_id: currentSessionId.value
        }

        wsConnection.send(JSON.stringify(message))

        scans.value.unshift({
            content: randomCode,
            timestamp: timestamp,
            sent: true
        })

        // Автопрокрутка
        if (autoScroll.value) {
            nextTick(() => {
                if (scansList.value) {
                    scansList.value.scrollTop = 0
                }
            })
        }

        showNotification(`Отсканировано: ${randomCode}`, 'success')
        playBeep()

    } catch (error) {
        console.error('Send error:', error)

        scans.value.unshift({
            content: randomCode,
            timestamp: timestamp,
            sent: false,
            error: error.message
        })

        showNotification('Ошибка отправки', 'error')
    }

    // Ограничиваем историю
    if (scans.value.length > 50) {
        scans.value = scans.value.slice(0, 50)
    }
}

// Тестовое сканирование
const testScan = () => {
    if (!isConnected.value) {
        showNotification('Сначала подключитесь к компьютеру', 'error')
        return
    }

    emulateQrScan()
}

// Отключение
const disconnect = () => {
    if (wsConnection) {
        wsConnection.close()
        wsConnection = null
    }

    isConnected.value = false
    isScannerActive.value = false
    currentSessionId.value = ''
    manualSessionId.value = ''

    // Возвращаемся к сканированию подключения
    if (isCameraActive.value) {
        startConnectionScanning()
    }

    showNotification('Отключено от компьютера', 'info')
}

// Очистка истории
const clearScans = () => {
    scans.value = []
    showNotification('История очищена', 'info')
}

// Переключение автопрокрутки
const toggleAutoScroll = () => {
    autoScroll.value = !autoScroll.value
    showNotification(`Автопрокрутка: ${autoScroll.value ? 'ВКЛ' : 'ВЫКЛ'}`, 'info')
}

// Воспроизведение звука
const playBeep = () => {
    try {
        // Простой звук через AudioContext
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()

        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)

        oscillator.frequency.value = 800
        oscillator.type = 'sine'

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1)

        oscillator.start(audioContext.currentTime)
        oscillator.stop(audioContext.currentTime + 0.1)

    } catch (error) {
        // Игнорируем ошибки аудио
    }
}

// Уведомления
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

// Форматирование
const truncateText = (text, maxLength = 30) => {
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

// Computed
const sentScansCount = computed(() => {
    return scans.value.filter(scan => scan.sent).length
})

const errorScansCount = computed(() => {
    return scans.value.filter(scan => !scan.sent).length
})

// Жизненный цикл
onMounted(() => {
    // Проверяем, есть ли сохраненная сессия
    const savedSession = localStorage.getItem('phone_scanner_session')
    if (savedSession) {
        manualSessionId.value = savedSession
    }
})

onUnmounted(() => {
    stopCamera()

    if (wsConnection) {
        wsConnection.close()
    }

    if (scanInterval) {
        clearInterval(scanInterval)
    }
})

// Watch
watch(currentSessionId, (newVal) => {
    if (newVal) {
        localStorage.setItem('phone_scanner_session', newVal)
    } else {
        localStorage.removeItem('phone_scanner_session')
    }
})

watch(isConnected, (newVal) => {
    if (!newVal && isCameraActive.value) {
        startConnectionScanning()
    }
})
</script>

<style scoped>
.phone-scanner-view {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    background: #121212;
    color: white;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.header {
    text-align: center;
    padding: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header h1 {
    font-size: 1.4rem;
    margin: 0.5rem 0;
}

.header p {
    opacity: 0.9;
    margin: 0;
    font-size: 0.9rem;
}

/* Камера выключена */
.camera-off-section,
.connect-section,
.scanner-section {
    flex: 1;
    padding: 1rem;
}

.camera-off-card {
    text-align: center;
    padding: 2rem 1rem;
    max-width: 400px;
    margin: 0 auto;
}

.camera-off-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.7;
}

.camera-off-card h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.3rem;
}

.camera-off-card p {
    margin-bottom: 2rem;
    opacity: 0.8;
}

.camera-tips {
    margin-top: 2rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    text-align: left;
}

.camera-tips ul {
    margin: 0.5rem 0;
    padding-left: 1.2rem;
}

.camera-tips li {
    margin-bottom: 0.3rem;
    font-size: 0.9rem;
}

/* Превью камеры */
.camera-preview,
.scanner-preview {
    position: relative;
    width: 100%;
    height: 300px;
    border-radius: 12px;
    overflow: hidden;
    background: #000;
    margin: 1rem 0;
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
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.scan-frame {
    width: 70%;
    height: 50%;
    border: 3px solid #00ff00;
    border-radius: 10px;
    box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.7);
}

.scan-text,
.scan-counter {
    color: white;
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: rgba(0, 0, 0, 0.7);
    border-radius: 20px;
    font-weight: 500;
}

.scan-counter {
    margin-top: 0.5rem;
    font-size: 0.9rem;
}

/* Управление камерой */
.camera-controls,
.scanner-controls {
    display: flex;
    gap: 0.5rem;
    margin: 1rem 0;
    flex-wrap: wrap;
    justify-content: center;
}

/* Информация о подключении */
.connection-info {
    margin-bottom: 1rem;
}

.info-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.info-card h3 {
    margin: 0;
    color: #4CAF50;
    font-size: 1.2rem;
}

.info-card p {
    margin: 0.5rem 0;
    opacity: 0.8;
}

.session-info {
    margin: 0.5rem 0;
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 6px;
    font-family: 'Courier New', monospace;
    word-break: break-all;
    font-size: 0.9rem;
}

.connection-stats {
    display: flex;
    gap: 1rem;
    margin-top: 0.5rem;
    font-size: 0.9rem;
    opacity: 0.8;
}

/* Сканер неактивен */
.scanner-inactive {
    text-align: center;
    padding: 2rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    margin: 1rem 0;
}

.inactive-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.scanner-inactive h4 {
    margin: 0 0 0.5rem 0;
}

.scanner-inactive p {
    margin: 0.5rem 0;
    opacity: 0.8;
}

/* История сканирований */
.scans-log {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
}

.log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.log-header h4 {
    margin: 0;
    font-size: 1.1rem;
}

.log-controls {
    display: flex;
    gap: 0.5rem;
}

.empty-scans {
    text-align: center;
    padding: 2rem 1rem;
    opacity: 0.5;
}

.empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.scans-list {
    max-height: 300px;
    overflow-y: auto;
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.2);
}

.scan-item {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    gap: 0.75rem;
    transition: background 0.2s;
    cursor: help;
}

.scan-item:hover {
    background: rgba(255, 255, 255, 0.05);
}

.scan-item:last-child {
    border-bottom: none;
}

.scan-item.scan-error {
    background: rgba(255, 0, 0, 0.1);
}

.scan-index {
    min-width: 30px;
    font-size: 0.8rem;
    opacity: 0.6;
    font-family: monospace;
}

.scan-time {
    min-width: 70px;
    font-size: 0.85rem;
    opacity: 0.8;
    font-family: monospace;
}

.scan-content {
    flex: 1;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    word-break: break-all;
}

.scan-status {
    min-width: 30px;
    text-align: center;
    font-weight: bold;
    font-size: 1.2rem;
}

.status-sent {
    color: #4CAF50;
}

.status-error {
    color: #f44336;
}

.log-summary {
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    text-align: center;
    font-size: 0.9rem;
    opacity: 0.7;
}

/* Статус бар */
.status-bar {
    display: flex;
    justify-content: space-around;
    padding: 0.75rem;
    background: rgba(0, 0, 0, 0.3);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.status-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
}

.status-icon {
    font-size: 1.5rem;
}

.status-text {
    font-size: 0.75rem;
    opacity: 0.8;
}

/* Уведомления */
.notification {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    z-index: 1000;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    animation: slideUp 0.3s ease-out;
    max-width: 90%;
    cursor: pointer;
}

.notification.info {
    border-left: 4px solid #2196F3;
}

.notification.success {
    border-left: 4px solid #4CAF50;
}

.notification.error {
    border-left: 4px solid #f44336;
}

.notification-icon {
    font-size: 1.2rem;
}

.notification-message {
    flex: 1;
    font-size: 0.95rem;
}

.notification-close {
    font-size: 1.5rem;
    opacity: 0.7;
}

@keyframes slideUp {
    from {
        transform: translate(-50%, 100%);
        opacity: 0;
    }

    to {
        transform: translate(-50%, 0);
        opacity: 1;
    }
}

/* Прогресс */
.processing-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1001;
}

.processing-spinner {
    width: 50px;
    height: 50px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-top-color: #2196F3;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.processing-text {
    margin-top: 1rem;
    color: white;
    font-size: 1rem;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Ручной ввод */
.manual-connect {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.manual-input {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.75rem;
}

.manual-input input {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.2s;
}

.manual-input input:focus {
    border-color: #2196F3;
}

.manual-input input::placeholder {
    color: rgba(255, 255, 255, 0.5);
}

/* Кнопки */
.btn {
    padding: 0.75rem 1.25rem;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: #2196F3;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #1976D2;
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.2);
}

.btn-success {
    background: #4CAF50;
    color: white;
}

.btn-success:hover:not(:disabled) {
    background: #388E3C;
}

.btn-danger {
    background: #f44336;
    color: white;
}

.btn-danger:hover:not(:disabled) {
    background: #d32f2f;
}

.btn-info {
    background: #00BCD4;
    color: white;
}

.btn-info:hover:not(:disabled) {
    background: #0097A7;
}

.btn-small {
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
}

.btn-lg {
    padding: 1rem 2rem;
    font-size: 1.1rem;
}

/* Адаптивность */
@media (max-width: 768px) {

    .camera-preview,
    .scanner-preview {
        height: 250px;
    }

    .camera-controls,
    .scanner-controls {
        flex-direction: column;
    }

    .btn {
        width: 100%;
    }

    .scan-item {
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .scan-time,
    .scan-index {
        min-width: auto;
    }
}
</style>