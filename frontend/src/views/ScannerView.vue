<template>
    <div class="scanner-view">
        <!-- Mode switcher -->
        <div class="mode-switcher">
            <button @click="mode = 'scanner'" :class="['mode-btn', mode === 'scanner' ? 'mode-btn-active' : '']">
                <span class="mode-icon">📟</span>
                <span>Сканер</span>
            </button>
            <button @click="mode = 'camera'" :class="['mode-btn', mode === 'camera' ? 'mode-btn-active' : '']">
                <span class="mode-icon">📷</span>
                <span>Камера</span>
            </button>
        </div>

        <!-- Scanner mode -->
        <div v-if="mode === 'scanner'" class="scanner-section">
            <div class="section-header">
                <h2>Сканирование сканером</h2>
            </div>

            <div class="scanner-input-section">
                <input id="scannerInput" v-model="scannerInput" placeholder="Наведите сканер на QR-код..."
                    @keydown.enter="processScannerInput" ref="scannerInputRef" class="scanner-input" autofocus />
            </div>
        </div>

        <!-- Camera mode -->
        <div v-else class="camera-section">
            <div class="section-header">
                <h2>Сканирование камерой</h2>
            </div>

            <!-- Переключатель режима камеры -->
            <div class="camera-mode-switcher">
                <button @click="cameraMode = 'local'"
                    :class="['camera-mode-btn', cameraMode === 'local' ? 'mode-btn-active' : '']">
                    <span class="mode-icon">📱</span>
                    <span>Локальная камера</span>
                </button>
                <button @click="cameraMode = 'remote'"
                    :class="['camera-mode-btn', cameraMode === 'remote' ? 'mode-btn-active' : '']">
                    <span class="mode-icon">📲</span>
                    <span>Камера телефона</span>
                </button>
            </div>

            <!-- Локальная камера -->
            <div v-if="cameraMode === 'local'" class="local-camera-section">
                <div class="camera-controls">
                    <button @click="toggleLocalCamera"
                        :class="['camera-toggle-btn', isLocalCameraActive ? 'btn-danger' : 'btn-success']">
                        {{ isLocalCameraActive ? 'Выключить камеру' : 'Включить камеру' }}
                    </button>
                </div>

                <div v-if="isLocalCameraActive" class="camera-preview">
                    <video ref="localVideoElement" autoplay playsinline class="camera-video"></video>
                    <div class="scan-overlay">
                        <div class="scan-frame"></div>
                    </div>

                    <div class="camera-actions">
                        <button @click="capturePhoto" class="btn btn-primary">
                            📸 Сканировать QR-код
                        </button>
                    </div>
                </div>
            </div>

            <!-- Удаленная камера (телефон) -->
            <div v-else class="remote-camera-section">
                <div v-if="!remoteSessionId" class="remote-setup">
                    <div class="setup-card">
                        <h3>Подключить камеру телефона</h3>
                        <p class="setup-description">
                            1. Нажмите кнопку ниже, чтобы создать QR-код подключения<br>
                            2. Откройте приложение на телефоне<br>
                            3. Во вкладке "Камера" выберите "Камера телефона"<br>
                            4. Нажмите "Подключиться к компьютеру" и отсканируйте QR-код
                        </p>

                        <button @click="generateRemoteSession" class="btn btn-primary btn-lg">
                            🔗 Создать подключение
                        </button>
                    </div>
                </div>

                <div v-else class="remote-session">
                    <div class="session-info">
                        <h3>Ожидание подключения телефона...</h3>
                        <p>Отсканируйте этот QR-код на телефоне</p>

                        <div class="qr-container">
                            <img :src="remoteQrCode" alt="QR код подключения" class="connection-qr" />
                            <div class="session-id">
                                ID сессии: <code>{{ remoteSessionId }}</code>
                            </div>
                        </div>

                        <div class="connection-status">
                            <div v-if="isPhoneConnected" class="status-connected">
                                <span class="status-icon">✅</span>
                                <span>Телефон подключен</span>
                            </div>
                            <div v-else class="status-disconnected">
                                <span class="status-icon">⏳</span>
                                <span>Ожидание подключения телефона...</span>
                            </div>
                        </div>

                        <div class="session-actions">
                            <button @click="copySessionId" class="btn btn-secondary">
                                📋 Копировать ID
                            </button>
                            <button @click="disconnectRemoteSession" class="btn btn-danger">
                                ✖️ Отключить
                            </button>
                        </div>
                    </div>

                    <!-- Лог сканирований с телефона -->
                    <div v-if="remoteScans.length > 0" class="remote-scans-log">
                        <h4>Отсканировано с телефона:</h4>
                        <div class="scans-list">
                            <div v-for="(scan, index) in remoteScans" :key="index" class="scan-item">
                                <span class="scan-time">{{ formatTime(scan.timestamp) }}</span>
                                <span class="scan-content">{{ truncateText(scan.content, 30) }}</span>
                                <span :class="['scan-status', scan.printed ? 'status-printed' : 'status-pending']">
                                    {{ scan.printed ? '✓' : '...' }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Actions -->
        <div class="actions-section">
            <button @click="testPrint" class="btn btn-secondary">
                🖨️ Тестовая печать
            </button>
            <button @click="openPrintWindow" class="btn btn-info">
                🔧 Открыть настройки печати
            </button>
        </div>

        <!-- Last scan info -->
        <div v-if="lastScan" class="last-scan-info">
            <div class="info-row">
                <span class="info-label">Последний код:</span>
                <span class="info-value">{{ truncateText(lastScan.qr_content, 40) }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Время:</span>
                <span class="info-value">{{ formatTime(lastScan.scanned_at) }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Статус:</span>
                <span :class="['tag', getStatusClass(lastScan.print_status)]">
                    {{ getStatusText(lastScan.print_status) }}
                </span>
            </div>
        </div>

        <!-- Status bar -->
        <div class="status-bar">
            <div class="status-item">
                <span class="status-icon">🖨️</span>
                <span class="status-text">Браузерная печать</span>
            </div>
            <div class="status-item">
                <span class="status-icon">📊</span>
                <span class="status-text">Сканов: {{ totalScans }}</span>
            </div>
            <div class="status-item">
                <span class="status-icon">{{ isPhoneConnected ? '📱✅' : '📱' }}</span>
                <span class="status-text">{{ isPhoneConnected ? 'Телефон подключен' : 'Телефон не подключен' }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import axios from 'axios'

// Reactive variables
const mode = ref('scanner')
const scannerInput = ref('')
const scannerInputRef = ref(null)
const lastScan = ref(null)
const totalScans = ref(0)

// Camera variables
const cameraMode = ref('local') // 'local' или 'remote'
const isLocalCameraActive = ref(false)
const localVideoElement = ref(null)
let localCameraStream = null

// Remote camera variables
const remoteSessionId = ref(null)
const remoteQrCode = ref('')
const isPhoneConnected = ref(false)
const remoteScans = ref([])
let wsConnection = null

onMounted(() => {
    focusScannerInput()
    document.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
    document.removeEventListener('keydown', handleGlobalKeyDown)
    stopLocalCamera()
    disconnectWebSocket()
})

const focusScannerInput = () => {
    nextTick(() => {
        if (scannerInputRef.value) {
            scannerInputRef.value.focus()
        }
    })
}

const handleGlobalKeyDown = (event) => {
    if (mode.value === 'scanner' && event.key === 'Enter' && scannerInput.value.trim()) {
        event.preventDefault()
        processScannerInput()
    }
}

const processScannerInput = async () => {
    const qrContent = scannerInput.value.trim()
    if (!qrContent) return

    await processScan(qrContent, 'scanner')
    scannerInput.value = ''
    focusScannerInput()
}

// Локальная камера
const toggleLocalCamera = async () => {
    if (isLocalCameraActive.value) {
        stopLocalCamera()
    } else {
        await startLocalCamera()
    }
}

const startLocalCamera = async () => {
    try {
        const constraints = {
            video: {
                facingMode: { ideal: 'environment' },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        }

        localCameraStream = await navigator.mediaDevices.getUserMedia(constraints)

        if (localVideoElement.value) {
            localVideoElement.value.srcObject = localCameraStream
            isLocalCameraActive.value = true
        }
    } catch (error) {
        console.error('Error starting camera:', error)
    }
}

const stopLocalCamera = () => {
    if (localCameraStream) {
        localCameraStream.getTracks().forEach(track => track.stop())
        localCameraStream = null
    }
    if (localVideoElement.value) {
        localVideoElement.value.srcObject = null
    }
    isLocalCameraActive.value = false
}

const capturePhoto = async () => {
    if (!localVideoElement.value || !isLocalCameraActive.value) return

    try {
        const canvas = document.createElement('canvas')
        canvas.width = localVideoElement.value.videoWidth
        canvas.height = localVideoElement.value.videoHeight

        const ctx = canvas.getContext('2d')
        ctx.drawImage(localVideoElement.value, 0, 0, canvas.width, canvas.height)

        canvas.toBlob(async (blob) => {
            const formData = new FormData()
            formData.append('image', blob, 'photo.jpg')

            const response = await axios.post('/api/scans/scan-image/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })

            if (response.data && response.data.qr_content) {
                await processScan(response.data.qr_content, 'local_camera')
                playBeep()
                stopLocalCamera()
            }
        }, 'image/jpeg', 0.8)

    } catch (error) {
        console.error('Error capturing photo:', error)
    }
}

// Удаленная камера (телефон)
const generateRemoteSession = async () => {
    try {
        // Генерируем уникальный ID сессии
        const sessionId = 'rs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
        remoteSessionId.value = sessionId

        // Создаем данные для QR-кода
        const qrData = {
            sessionId: sessionId,
            type: 'remote_scanner_connect',
            timestamp: new Date().toISOString(),
            url: window.location.hostname
        }

        const qrContent = JSON.stringify(qrData)

        // Генерируем QR-код
        const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(qrContent)}&format=png&margin=10&color=0-0-0&bgcolor=255-255-255`

        // Альтернативно, можно использовать локальную генерацию QR-кода
        // const qrCodeUrl = `/api/generate-qr?data=${encodeURIComponent(qrContent)}`

        remoteQrCode.value = qrCodeUrl

        // Подключаемся к WebSocket как хост
        connectWebSocket(sessionId, 'host')

        alert('✅ QR-код для подключения создан! Отсканируйте его на телефоне.')

    } catch (error) {
        console.error('Error generating remote session:', error)
        alert('Ошибка создания подключения: ' + error.message)
    }
}

const connectWebSocket = (sessionId, deviceType) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/remote-scanner/${sessionId}/${deviceType}`

    wsConnection = new WebSocket(wsUrl)

    wsConnection.onopen = () => {
        console.log('WebSocket connected as', deviceType)
        if (deviceType === 'host') {
            checkConnectionStatus()
        }
    }

    wsConnection.onmessage = async (event) => {
        const message = JSON.parse(event.data)

        switch (message.type) {
            case 'status':
                if (message.status === 'client_connected') {
                    isPhoneConnected.value = true
                    playBeep()
                } else if (message.status === 'client_disconnected') {
                    isPhoneConnected.value = false
                }
                break

            case 'scan':
                if (message.qr_content && deviceType === 'host') {
                    // Получили сканирование с телефона
                    remoteScans.value.unshift({
                        content: message.qr_content,
                        timestamp: new Date(),
                        printed: false
                    })

                    // Обрабатываем сканирование
                    await processScan(message.qr_content, 'remote_phone')

                    // Отмечаем как напечатанное
                    const lastScan = remoteScans.value[0]
                    lastScan.printed = true
                }
                break
        }
    }

    wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error)
    }

    wsConnection.onclose = () => {
        console.log('WebSocket disconnected')
        isPhoneConnected.value = false
    }
}

const disconnectWebSocket = () => {
    if (wsConnection) {
        wsConnection.close()
        wsConnection = null
    }
}

const checkConnectionStatus = async () => {
    if (!remoteSessionId.value) return

    try {
        const response = await axios.get(`/ws/sessions/${remoteSessionId.value}/status`)
        isPhoneConnected.value = response.data.client_connected

        if (isPhoneConnected.value) {
            setTimeout(checkConnectionStatus, 5000) // Проверяем каждые 5 секунд
        }
    } catch (error) {
        console.error('Error checking connection status:', error)
    }
}

const copySessionId = () => {
    navigator.clipboard.writeText(remoteSessionId.value)
    alert('ID сессии скопирован в буфер обмена')
}

const disconnectRemoteSession = () => {
    remoteSessionId.value = null
    remoteQrCode.value = ''
    isPhoneConnected.value = false
    remoteScans.value = []
    disconnectWebSocket()
}

const processScan = async (qrContent, source) => {
    try {
        playBeep()

        const response = await axios.post('/api/scans/', {
            qr_content: qrContent,
            scan_source: source
        })

        lastScan.value = response.data
        totalScans.value++

        // Автоматически печатаем
        await printQrCode(qrContent)

    } catch (error) {
        console.error('Scan error:', error)
    }
}

const testPrint = () => {
    printTestPage()
}

const openPrintWindow = () => {
    const printWindow = window.open('/printers', '_blank')
    if (printWindow) {
        printWindow.focus()
    }
}

const printQrCode = async (qrContent) => {
    try {
        const printWindow = window.open('', '_blank')

        const htmlContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Печать QR-кода</title>
                <style>
                    @media print {
                        body { margin: 0; padding: 0; }
                    }
                    body {
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 10mm;
                    }
                    .qr-container {
                        margin: 0 auto;
                        max-width: 80mm;
                    }
                    .qr-image {
                        width: 50mm;
                        height: 50mm;
                        margin: 5mm auto;
                        display: block;
                    }
                    .qr-content {
                        margin-top: 3mm;
                        padding: 2mm;
                        background: #f5f5f5;
                        border-radius: 2mm;
                        word-break: break-all;
                        font-family: monospace;
                        font-size: 9pt;
                    }
                    .print-info {
                        margin-top: 2mm;
                        color: #666;
                        font-size: 8pt;
                    }
                </style>
            </head>
            <body>
                <div class="qr-container">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(qrContent)}" 
                         alt="QR Code" class="qr-image" />
                    <div class="qr-content">
                        ${qrContent}
                    </div>
                    <div class="print-info">
                        ${new Date().toLocaleString('ru-RU')}
                    </div>
                </div>
                <script>
                    window.onload = function() {
                        window.print();
                    };
                <\/script>
            </body>
            </html>
        `

        printWindow.document.write(htmlContent)
        printWindow.document.close()

    } catch (error) {
        console.error('Print error:', error)
    }
}

const printTestPage = () => {
    const printWindow = window.open('', '_blank')

    const testHTML = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Тестовая печать</title>
            <style>
                @media print {
                    body { margin: 0; padding: 0; }
                }
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 20mm;
                }
                .test-content {
                    border: 1px solid #ccc;
                    padding: 10mm;
                    margin: 0 auto;
                    max-width: 80mm;
                }
                h1 { 
                    color: #333; 
                    font-size: 16pt;
                    margin: 0 0 5mm 0;
                }
                .test-info {
                    margin: 5mm 0;
                    padding: 3mm;
                    background: #f9f9f9;
                    border-radius: 2mm;
                    font-size: 10pt;
                }
                .instructions {
                    text-align: left;
                    margin: 5mm 0;
                    padding: 3mm;
                    border: 1px dashed #ccc;
                    border-radius: 2mm;
                    font-size: 9pt;
                }
            </style>
        </head>
        <body>
            <div class="test-content">
                <h1>ТЕСТОВАЯ ПЕЧАТЬ</h1>
                <div class="test-info">
                    <p><strong>Система:</strong> QR Replication System</p>
                    <p><strong>Дата:</strong> ${new Date().toLocaleDateString('ru-RU')}</p>
                    <p><strong>Время:</strong> ${new Date().toLocaleTimeString('ru-RU')}</p>
                </div>
                
                <div class="instructions">
                    <p><strong>Инструкция по тестированию:</strong></p>
                    <ol>
                        <li>Убедитесь, что выбран правильный принтер</li>
                        <li>Проверьте настройки бумаги (размер, ориентация)</li>
                        <li>Нажмите "Печать" в диалоговом окне</li>
                        <li>Проверьте качество отпечатка</li>
                    </ol>
                </div>
                
                <div style="margin-top: 10mm; font-size: 8pt; color: #666;">
                    Если этот текст печатается четко, система работает корректно.
                </div>
            </div>
            <script>
                window.onload = function() {
                    window.print();
                };
            <\/script>
        </body>
        </html>
    `

    printWindow.document.write(testHTML)
    printWindow.document.close()
}

const playBeep = () => {
    try {
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
    } catch (e) {
        // Audio not supported
    }
}

const truncateText = (text, maxLength) => {
    if (!text) return ''
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
}

const formatTime = (dateOrString) => {
    if (!dateOrString) return ''
    const date = typeof dateOrString === 'string' ? new Date(dateOrString) : dateOrString
    return date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
    })
}

const getStatusClass = (status) => {
    const map = {
        'success': 'tag-success',
        'pending': 'tag-warning',
        'failed': 'tag-danger'
    }
    return map[status] || 'tag-info'
}

const getStatusText = (status) => {
    const map = {
        'success': 'Напечатан',
        'pending': 'В ожидании',
        'failed': 'Ошибка'
    }
    return map[status] || status
}
</script>

<style scoped>
.scanner-view {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-height: 100vh;
    padding: 1rem;
    background: #f8f9fa;
}

.mode-switcher {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.mode-btn {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid #ddd;
    border-radius: 6px;
    background: white;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.2s;
    font-weight: 500;
}

.mode-btn:hover {
    border-color: #007bff;
}

.mode-btn-active {
    border-color: #007bff;
    background: #f0f4ff;
}

.mode-icon {
    font-size: 1.5rem;
}

.scanner-section,
.camera-section {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-header {
    margin-bottom: 1rem;
}

.section-header h2 {
    color: #333;
    font-size: 1.2rem;
    font-weight: 600;
}

.camera-mode-switcher {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}

.camera-mode-btn {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid #ddd;
    border-radius: 6px;
    background: white;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.2s;
    font-weight: 500;
}

.camera-mode-btn:hover {
    border-color: #28a745;
}

.camera-mode-btn.mode-btn-active {
    border-color: #28a745;
    background: #f0f9f0;
}

.local-camera-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.remote-camera-section {
    min-height: 400px;
}

.setup-card {
    text-align: center;
    padding: 2rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 2px dashed #dee2e6;
}

.setup-description {
    margin: 1.5rem 0;
    color: #666;
    line-height: 1.6;
    text-align: left;
}

.btn-lg {
    padding: 1rem 2rem;
    font-size: 1.1rem;
}

.remote-session {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.session-info {
    text-align: center;
    padding: 1.5rem;
    background: white;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.qr-container {
    margin: 1.5rem auto;
    padding: 1rem;
    background: white;
    border-radius: 8px;
    display: inline-block;
    border: 1px solid #ddd;
}

.connection-qr {
    width: 200px;
    height: 200px;
    display: block;
    margin: 0 auto;
}

.session-id {
    margin-top: 1rem;
    padding: 0.5rem;
    background: #f8f9fa;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.9rem;
}

.connection-status {
    margin: 1rem 0;
    padding: 1rem;
    border-radius: 8px;
    background: #f8f9fa;
}

.status-connected {
    color: #28a745;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.status-disconnected {
    color: #6c757d;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.session-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    margin-top: 1rem;
}

.remote-scans-log {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    border: 1px solid #dee2e6;
}

.remote-scans-log h4 {
    margin: 0 0 1rem 0;
    color: #333;
}

.scans-list {
    max-height: 200px;
    overflow-y: auto;
}

.scan-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border-bottom: 1px solid #f0f0f0;
    gap: 1rem;
}

.scan-item:last-child {
    border-bottom: none;
}

.scan-time {
    color: #666;
    font-size: 0.9rem;
    min-width: 60px;
}

.scan-content {
    flex: 1;
    font-family: monospace;
    font-size: 0.95rem;
    word-break: break-all;
}

.scan-status {
    font-weight: bold;
    min-width: 20px;
}

.status-printed {
    color: #28a745;
}

.status-pending {
    color: #ffc107;
}

.scanner-input {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #007bff;
    border-radius: 6px;
    font-size: 1rem;
    text-align: center;
    transition: border-color 0.2s;
}

.scanner-input:focus {
    outline: none;
    border-color: #0056b3;
}

.camera-controls {
    display: flex;
    justify-content: center;
    margin-bottom: 1rem;
}

.camera-toggle-btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
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

.camera-preview {
    position: relative;
    margin: 1rem 0;
}

.camera-video {
    width: 100%;
    max-height: 400px;
    border-radius: 8px;
    border: 2px solid #ddd;
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

.camera-actions {
    display: flex;
    justify-content: center;
    margin-top: 1rem;
}

.actions-section {
    display: flex;
    gap: 1rem;
    background: white;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    flex: 1;
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

.btn-info {
    background: #17a2b8;
    color: white;
}

.btn-info:hover {
    background: #138496;
}

.btn-danger {
    background: #dc3545;
    color: white;
}

.btn-danger:hover {
    background: #c82333;
}

.last-scan-info {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.info-row {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
    gap: 0.5rem;
}

.info-label {
    font-weight: 600;
    color: #555;
    min-width: 100px;
}

.info-value {
    word-break: break-all;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
}

.tag {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.85rem;
    font-weight: 500;
    border-radius: 4px;
}

.tag-success {
    background: #d4edda;
    color: #155724;
}

.tag-warning {
    background: #fff3cd;
    color: #856404;
}

.tag-danger {
    background: #f8d7da;
    color: #721c24;
}

.status-bar {
    display: flex;
    justify-content: space-between;
    background: white;
    border-radius: 8px;
    padding: 0.75rem;
    margin-top: auto;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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
    color: #666;
}

@media (max-width: 768px) {
    .scanner-view {
        padding: 0.5rem;
    }

    .actions-section {
        flex-direction: column;
    }

    .status-bar {
        flex-direction: column;
        gap: 0.5rem;
    }

    .camera-mode-switcher {
        flex-direction: column;
    }

    .session-actions {
        flex-direction: column;
    }

    .connection-qr {
        width: 150px;
        height: 150px;
    }
}
</style>