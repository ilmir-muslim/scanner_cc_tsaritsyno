<template>
    <div class="scanner-view">
        <!-- Mode switcher -->
        <div class="mode-switcher">
            <button @click="mode = 'scanner'" :class="['mode-btn', mode === 'scanner' ? 'mode-btn-active' : '']">
                <span class="mode-icon">📟</span>
                <span>Сканер S20-B</span>
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

            <div class="scanner-instructions">
                <p><strong>Инструкция:</strong></p>
                <ol>
                    <li>Подключите сканер S20-B по USB или Bluetooth</li>
                    <li>Наведите сканер на QR-код</li>
                    <li>Сканер автоматически отправит код в поле ниже</li>
                </ol>
            </div>

            <div class="scanner-input-section">
                <label for="scannerInput">Поле для сканирования:</label>
                <input id="scannerInput" v-model="scannerInput" placeholder="Наведите сканер на QR-код..."
                    @keydown.enter="processScannerInput" ref="scannerInputRef" class="scanner-input" autofocus />
                <small class="input-hint">
                    Сканер автоматически добавит код и нажмёт Enter. Или введите вручную и нажмите Enter.
                </small>
            </div>
        </div>

        <!-- Camera mode -->
        <div v-else class="camera-section">
            <div class="section-header">
                <h2>Сканирование камерой</h2>
            </div>

            <div class="camera-controls">
                <button @click="toggleCamera"
                    :class="['camera-toggle-btn', isCameraActive ? 'btn-danger' : 'btn-success']">
                    {{ isCameraActive ? 'Выключить камеру' : 'Включить камеру' }}
                </button>

                <select v-model="selectedCamera" :disabled="isCameraActive" class="camera-select">
                    <option value="">Выберите камеру</option>
                    <option v-for="camera in availableCameras" :key="camera.deviceId" :value="camera.deviceId">
                        {{ camera.label }}
                    </option>
                </select>
            </div>

            <div v-if="isCameraActive" class="camera-preview">
                <video ref="videoElement" autoplay playsinline class="camera-video"></video>
                <div class="scan-overlay">
                    <div class="scan-frame"></div>
                    <p class="scan-hint">Наведите камеру на QR-код</p>
                </div>

                <div class="camera-actions">
                    <button @click="capturePhoto" class="btn btn-info">
                        📸 Сделать снимок
                    </button>
                    <button @click="uploadImage" class="btn btn-secondary">
                        📤 Загрузить изображение
                    </button>
                    <input ref="fileInput" type="file" accept="image/*" @change="handleFileUpload"
                        style="display: none;" />
                </div>
            </div>

            <div v-else class="camera-placeholder">
                <div class="placeholder-icon">📷</div>
                <p>Нажмите "Включить камеру" для начала сканирования</p>
            </div>
        </div>

        <!-- Last scanned code -->
        <div v-if="lastScan" class="last-scan">
            <div class="section-header">
                <h2>Последний отсканированный код</h2>
            </div>

            <div class="scan-details">
                <div class="qr-preview">
                    <img v-if="lastScan.qr_image" :src="lastScan.qr_image" alt="QR Code" class="qr-image" />
                    <div v-else class="qr-placeholder">
                        <span class="qr-placeholder-icon">QR</span>
                    </div>
                </div>

                <div class="scan-info">
                    <div class="info-row">
                        <span class="info-label">Содержимое:</span>
                        <code class="info-value">{{ lastScan.qr_content }}</code>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Источник:</span>
                        <span :class="['tag', lastScan.scan_source === 'scanner' ? 'tag-info' : 'tag-warning']">
                            {{ lastScan.scan_source === 'scanner' ? 'Сканер' : 'Камера' }}
                        </span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Время:</span>
                        <span class="info-value">{{ formatDateTime(lastScan.scanned_at) }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Статус печати:</span>
                        <span :class="['tag', getStatusClass(lastScan.print_status)]">
                            {{ lastScan.print_status }}
                        </span>
                    </div>

                    <div class="action-buttons">
                        <button @click="reprint(lastScan.qr_content)" class="btn btn-primary">
                            🖨️ Печатать снова
                        </button>
                        <button @click="copyToClipboard(lastScan.qr_content)" class="btn btn-secondary">
                            📋 Копировать код
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Printer status -->
        <div class="printer-status">
            <div class="section-header">
                <h2>Статус системы печати</h2>
            </div>

            <div class="printer-info">
                <div class="info-row">
                    <span class="info-label">Принтер:</span>
                    <span class="info-value">{{ printerName }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Статус:</span>
                    <span :class="['tag', printerReady ? 'tag-success' : 'tag-danger']">
                        {{ printerStatus }}
                    </span>
                </div>
                <div class="info-row">
                    <span class="info-label">Тип подключения:</span>
                    <span class="info-value">{{ printerConnectionType }}</span>
                </div>
            </div>

            <hr class="divider">

            <div class="printer-actions">
                <button @click="testPrint" :disabled="!printerReady" class="btn btn-outline">
                    🖨️ Тест печати
                </button>
                <button @click="$router.push('/printers')" class="btn btn-text">
                    ⚙️ Настройки принтеров
                </button>
            </div>
        </div>

        <!-- Toast notification -->
        <div v-if="toastVisible" :class="['toast', `toast-${toastType}`]">
            {{ toastMessage }}
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// Reactive variables
const mode = ref('scanner')
const scannerInput = ref('')
const scannerInputRef = ref(null)
const lastScan = ref(null)

// Camera variables
const isCameraActive = ref(false)
const selectedCamera = ref('')
const availableCameras = ref([])
const videoElement = ref(null)
const fileInput = ref(null)

// Printer variables
const printerStatus = ref('Проверка...')
const printerName = ref('Не выбран')
const printerConnectionType = ref('-')
const printerReady = ref(false)

// Toast variables
const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref('info')

// Store camera stream reference
let cameraStream = null

onMounted(() => {
    focusScannerInput()
    loadPrinterStatus()
    document.addEventListener('keydown', handleGlobalKeyDown)
    enumerateCameras()
})

onUnmounted(() => {
    document.removeEventListener('keydown', handleGlobalKeyDown)
    stopCamera()
})

// Toast methods
const showToast = (message, type = 'info') => {
    toastMessage.value = message
    toastType.value = type
    toastVisible.value = true
    setTimeout(() => {
        toastVisible.value = false
    }, 3000)
}

// Scanner methods
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

// Camera methods
const enumerateCameras = async () => {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const videoDevices = devices.filter(device => device.kind === 'videoinput')

        availableCameras.value = videoDevices.map(device => ({
            deviceId: device.deviceId,
            label: device.label || `Камера ${availableCameras.value.length + 1}`
        }))

        if (availableCameras.value.length > 0 && !selectedCamera.value) {
            selectedCamera.value = availableCameras.value[0].deviceId
        }
    } catch (error) {
        console.error('Error enumerating cameras:', error)
        showToast('Не удалось получить список камер', 'warning')
    }
}

const toggleCamera = async () => {
    if (isCameraActive.value) {
        stopCamera()
    } else {
        await startCamera()
    }
}

const startCamera = async () => {
    try {
        const constraints = {
            video: {
                deviceId: selectedCamera.value ? { exact: selectedCamera.value } : undefined,
                facingMode: { ideal: 'environment' },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        }

        cameraStream = await navigator.mediaDevices.getUserMedia(constraints)

        if (videoElement.value) {
            videoElement.value.srcObject = cameraStream
            isCameraActive.value = true
        }
    } catch (error) {
        console.error('Error starting camera:', error)
        showToast('Не удалось включить камеру. Проверьте разрешения.', 'error')
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
    isCameraActive.value = false
}

const capturePhoto = async () => {
    if (!videoElement.value || !isCameraActive.value) return

    try {
        const canvas = document.createElement('canvas')
        canvas.width = videoElement.value.videoWidth
        canvas.height = videoElement.value.videoHeight

        const ctx = canvas.getContext('2d')
        ctx.drawImage(videoElement.value, 0, 0, canvas.width, canvas.height)

        // Convert canvas to blob
        canvas.toBlob(async (blob) => {
            const formData = new FormData()
            formData.append('image', blob, 'photo.jpg')

            try {
                const response = await axios.post('/api/scans/scan-image/', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                })

                if (response.data && response.data.qr_content) {
                    lastScan.value = response.data
                    showToast('QR-код найден!', 'success')
                    playBeep()
                    stopCamera()
                } else {
                    showToast('QR-код не обнаружен на изображении', 'warning')
                }
            } catch (error) {
                console.error('Error uploading image:', error)
                showToast('Не удалось обработать изображение', 'error')
            }
        }, 'image/jpeg', 0.8)

    } catch (error) {
        console.error('Error capturing photo:', error)
        showToast('Не удалось сделать снимок', 'error')
    }
}

const uploadImage = () => {
    if (fileInput.value) {
        fileInput.value.click()
    }
}

const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('image', file)

    try {
        const response = await axios.post('/api/scans/scan-image/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })

        if (response.data) {
            lastScan.value = response.data
            showToast('QR-код найден в изображении!', 'success')
            playBeep()
        }
    } catch (error) {
        showToast('Не удалось найти QR-код в изображении', 'error')
    }

    // Clear input
    event.target.value = ''
}

// Common methods
const processScan = async (qrContent, source) => {
    try {
        playBeep()

        const response = await axios.post('/api/scans/', {
            qr_content: qrContent,
            scan_source: source
        })

        lastScan.value = response.data
        showToast('QR-код успешно отсканирован и отправлен на печать!', 'success')

    } catch (error) {
        console.error('Scan error:', error)
        showToast('Ошибка при обработке QR-кода', 'error')
    }
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

const loadPrinterStatus = async () => {
    try {
        const response = await axios.get('/api/printers/default')
        printerName.value = response.data.name
        printerConnectionType.value = response.data.connection_type
        printerStatus.value = 'Готов'
        printerReady.value = true
    } catch (error) {
        printerStatus.value = 'Недоступен'
        printerReady.value = false
    }
}

const testPrint = async () => {
    try {
        await axios.post('/api/printers/test/')
        showToast('Тестовое задание отправлено на принтер', 'success')
    } catch (error) {
        showToast('Ошибка тестовой печати', 'error')
    }
}

const reprint = async (qrContent) => {
    try {
        await axios.post('/api/scans/print-again/', {
            qr_content: qrContent
        })
        showToast('Задание на печать отправлено', 'success')
    } catch (error) {
        showToast('Ошибка при печати', 'error')
    }
}

const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
        .then(() => showToast('Скопировано в буфер обмена', 'success'))
        .catch(() => showToast('Ошибка копирования', 'error'))
}

const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU')
}

const getStatusClass = (status) => {
    const map = {
        'success': 'tag-success',
        'pending': 'tag-warning',
        'failed': 'tag-danger'
    }
    return map[status] || 'tag-info'
}
</script>

<style scoped>
.scanner-view {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.mode-switcher {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.mode-btn {
    flex: 1;
    padding: 1rem;
    border: 2px solid #ddd;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s;
}

.mode-btn:hover {
    border-color: #667eea;
}

.mode-btn-active {
    border-color: #667eea;
    background: #f0f4ff;
}

.mode-icon {
    font-size: 2rem;
}

.scanner-section,
.camera-section,
.last-scan,
.printer-status {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #f0f0f0;
}

.section-header h2 {
    color: #333;
    font-size: 1.5rem;
    font-weight: 600;
}

.scanner-instructions {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 1.5rem;
}

.scanner-instructions ol {
    padding-left: 1.5rem;
    margin-top: 0.5rem;
}

.scanner-instructions li {
    margin-bottom: 0.25rem;
}

.scanner-input-section {
    margin: 1.5rem 0;
}

.scanner-input-section label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #333;
}

.scanner-input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    transition: border-color 0.2s;
}

.scanner-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.input-hint {
    display: block;
    color: #666;
    font-style: italic;
    margin-top: 0.5rem;
}

.camera-controls {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.camera-toggle-btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
}

.camera-select {
    flex: 1;
    min-width: 200px;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: white;
}

.camera-preview {
    position: relative;
    margin: 1rem 0;
}

.camera-video {
    width: 100%;
    max-width: 640px;
    display: block;
    margin: 0 auto;
    border-radius: 8px;
    border: 2px solid #ddd;
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
    background: rgba(0, 0, 0, 0.3);
    pointer-events: none;
}

.scan-frame {
    width: 70%;
    height: 70%;
    border: 3px solid #fff;
    border-radius: 8px;
    box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.5);
}

.scan-hint {
    color: white;
    margin-top: 1rem;
    font-weight: 500;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
}

.camera-actions {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 1rem;
    flex-wrap: wrap;
}

.camera-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    background: #f8f9fa;
    border-radius: 8px;
    color: #666;
}

.placeholder-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
}

.scan-details {
    display: flex;
    gap: 2rem;
    align-items: flex-start;
}

@media (max-width: 768px) {
    .scan-details {
        flex-direction: column;
        align-items: center;
    }
}

.qr-preview {
    flex-shrink: 0;
}

.qr-image {
    width: 200px;
    height: 200px;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 8px;
    background: white;
}

.qr-placeholder {
    width: 200px;
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #ddd;
    border-radius: 4px;
    background: #f8f9fa;
}

.qr-placeholder-icon {
    font-size: 2rem;
    color: #999;
    font-weight: bold;
}

.scan-info {
    flex-grow: 1;
}

.info-row {
    display: flex;
    align-items: center;
    margin-bottom: 1rem;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.info-label {
    font-weight: 600;
    min-width: 140px;
    color: #555;
}

.info-value {
    word-break: break-all;
    font-family: 'Courier New', monospace;
    background: #f5f5f5;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
}

.tag {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.85rem;
    font-weight: 500;
    border-radius: 4px;
    white-space: nowrap;
}

.tag-success {
    background: #28a745;
    color: white;
}

.tag-warning {
    background: #ffc107;
    color: black;
}

.tag-danger {
    background: #dc3545;
    color: white;
}

.tag-info {
    background: #17a2b8;
    color: white;
}

.action-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
    flex-wrap: wrap;
}

.printer-info {
    margin-bottom: 1rem;
}

.divider {
    border: none;
    border-top: 1px solid #dee2e6;
    margin: 1rem 0;
}

.printer-actions {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
}

.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
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
    background: #545b62;
}

.btn-success {
    background: #28a745;
    color: white;
}

.btn-success:hover {
    background: #1e7e34;
}

.btn-danger {
    background: #dc3545;
    color: white;
}

.btn-danger:hover {
    background: #bd2130;
}

.btn-info {
    background: #17a2b8;
    color: white;
}

.btn-info:hover {
    background: #138496;
}

.btn-outline {
    background: transparent;
    border: 1px solid #007bff;
    color: #007bff;
}

.btn-outline:hover {
    background: #007bff;
    color: white;
}

.btn-text {
    background: transparent;
    color: #007bff;
    border: none;
}

.btn-text:hover {
    background: #f0f4ff;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn:disabled:hover {
    background: inherit;
    color: inherit;
}

.toast {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 4px;
    color: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    animation: slideIn 0.3s ease-out;
}

.toast-success {
    background: #28a745;
}

.toast-error {
    background: #dc3545;
}

.toast-warning {
    background: #ffc107;
    color: black;
}

.toast-info {
    background: #17a2b8;
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
</style>