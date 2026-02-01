<template>
    <div class="printers-view">
        <div class="section-header">
            <h1>Управление печатью</h1>
            <p>Используется браузерная печать по умолчанию</p>
        </div>

        <!-- Браузерная печать -->
        <div class="browser-print-section">
            <div class="browser-print-card">
                <div class="browser-print-header">
                    <div class="browser-print-icon">🌐</div>
                    <div>
                        <h3>Браузерная печать</h3>
                        <p class="browser-print-description">
                            Система использует стандартный диалог печати вашего браузера.
                            Печать выполняется на принтер, установленный по умолчанию в вашей операционной системе.
                        </p>
                    </div>
                </div>

                <div class="browser-print-info">
                    <h5>🎯 Как это работает:</h5>
                    <ul>
                        <li>QR-код генерируется на странице</li>
                        <li>Открывается стандартный диалог печати браузера</li>
                        <li>Вы выбираете принтер и настраиваете параметры печати</li>
                        <li>Печать выполняется через драйверы вашей системы</li>
                    </ul>
                </div>

                <div class="browser-print-actions">
                    <button @click="testBrowserPrint" class="btn btn-primary btn-lg">
                        🖨️ Тест печати
                    </button>

                    <div class="print-settings">
                        <div class="setting-group">
                            <label>Размер этикетки:</label>
                            <select v-model="labelSize" class="form-select">
                                <option value="50x30">50x30 мм</option>
                                <option value="70x50">70x50 мм</option>
                                <option value="100x70">100x70 мм</option>
                                <option value="A4">A4</option>
                            </select>
                        </div>

                        <div class="setting-group">
                            <label>Количество копий:</label>
                            <input type="number" v-model="copies" min="1" max="10" class="form-input" />
                        </div>
                    </div>
                </div>

                <!-- Принтер по умолчанию -->
                <div class="default-printer-info" v-if="defaultPrinter">
                    <h5>📋 Текущие настройки:</h5>
                    <div class="printer-details">
                        <div class="detail-row">
                            <span class="detail-label">Принтер:</span>
                            <span class="detail-value">{{ defaultPrinter.name }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Тип:</span>
                            <span class="detail-value">Браузерная печать</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Статус:</span>
                            <span class="status-tag status-success">Готов</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Список настроенных принтеров (только информационный) -->
        <div class="printers-section" v-if="printers.length > 0">
            <div class="section-subheader">
                <h2>Зарегистрированные принтеры</h2>
            </div>

            <div class="printers-grid">
                <div v-for="printer in printers" :key="printer.id" class="printer-card">
                    <div class="printer-header">
                        <div class="printer-title">
                            <h3>{{ printer.name }}</h3>
                            <div class="printer-badges">
                                <span v-if="printer.is_default" class="badge badge-primary">По умолчанию</span>
                                <span :class="['badge', printer.is_active ? 'badge-success' : 'badge-secondary']">
                                    {{ printer.is_active ? 'Активен' : 'Неактивен' }}
                                </span>
                            </div>
                        </div>
                        <div class="printer-type">
                            <span class="type-icon">
                                {{ printer.connection_type === 'browser' ? '🌐' : '🖨️' }}
                            </span>
                            <span class="type-text">
                                {{ printer.connection_type === 'browser' ? 'Браузерная печать' : 'Сетевой' }}
                            </span>
                        </div>
                    </div>

                    <div class="printer-info">
                        <div v-if="printer.ip_address" class="info-row">
                            <span class="info-label">IP адрес:</span>
                            <span class="info-value">{{ printer.ip_address }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Добавлен:</span>
                            <span class="info-value">{{ formatDate(printer.created_at) }}</span>
                        </div>
                    </div>

                    <div class="printer-actions">
                        <button @click="setDefaultPrinter(printer)" :disabled="printer.is_default" class="btn btn-icon"
                            title="Установить по умолчанию">
                            ⭐ По умолчанию
                        </button>
                        <button @click="deletePrinter(printer)" class="btn btn-icon btn-danger" title="Удалить">
                            🗑️ Удалить
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Toast -->
        <div v-if="toastVisible" :class="['toast', `toast-${toastType}`]">
            {{ toastMessage }}
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const printers = ref([])
const defaultPrinter = ref(null)
const labelSize = ref('50x30')
const copies = ref(1)

// Toast variables
const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref('info')

onMounted(() => {
    loadPrinters()
    loadDefaultPrinter()
})

const showToast = (message, type = 'info') => {
    toastMessage.value = message
    toastType.value = type
    toastVisible.value = true
    setTimeout(() => {
        toastVisible.value = false
    }, 3000)
}

const loadPrinters = async () => {
    try {
        const response = await axios.get('/api/printers/')
        printers.value = response.data.filter(p => p.is_active)
    } catch (error) {
        console.error('Failed to load printers:', error)
        printers.value = []
    }
}

const loadDefaultPrinter = async () => {
    try {
        const response = await axios.get('/api/printers/default')
        defaultPrinter.value = response.data
    } catch (error) {
        console.error('Failed to load default printer:', error)
        defaultPrinter.value = null
    }
}

const testBrowserPrint = () => {
    const printWindow = window.open('', '_blank')
    const testContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Тест печати</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                }
                .test-page {
                    border: 2px dashed #ccc;
                    padding: 30px;
                    border-radius: 10px;
                    margin: 20px auto;
                    max-width: 600px;
                }
                h1 { color: #333; }
                .success { color: green; font-size: 48px; margin: 20px; }
                .instructions {
                    text-align: left;
                    margin: 30px auto;
                    max-width: 500px;
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 5px;
                }
                .print-button {
                    padding: 15px 30px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 18px;
                    margin: 20px;
                }
            </style>
        </head>
        <body>
            <div class="test-page">
                <div class="success">✅</div>
                <h1>Тестовая страница печати</h1>
                <p>Если вы видите эту страницу, система печати работает корректно.</p>
                <p><strong>Дата:</strong> ${new Date().toLocaleDateString('ru-RU')}</p>
                <p><strong>Время:</strong> ${new Date().toLocaleTimeString('ru-RU')}</p>
                
                <div class="instructions">
                    <h3>Инструкция:</h3>
                    <ol>
                        <li>Нажмите кнопку "Печатать" ниже</li>
                        <li>В открывшемся диалоге выберите ваш принтер</li>
                        <li>Настройте параметры печати (количество копий, ориентацию)</li>
                        <li>Нажмите "Печать"</li>
                    </ol>
                </div>
                
                <button class="print-button" onclick="window.print()">
                    🖨️ Печатать
                </button>
                <button class="print-button" onclick="window.close()" 
                        style="background: #6c757d;">
                    ✖️ Закрыть
                </button>
            </div>
            
            <script>
                // Автоматически запускаем печать без подтверждения
                setTimeout(() => {
                    window.print();
                }, 500);
            <\/script>
        </body>
        </html>
    `

    printWindow.document.write(testContent)
    printWindow.document.close()

    showToast('Тестовая страница печати открыта', 'info')
}

const setDefaultPrinter = async (printer) => {
    try {
        const updateData = {
            name: printer.name,
            connection_type: printer.connection_type,
            ip_address: printer.ip_address,
            port: printer.port,
            is_default: true,
            is_active: true
        }

        await axios.put(`/api/printers/${printer.id}`, updateData)
        showToast(`Принтер "${printer.name}" установлен по умолчанию`, 'success')
        await loadPrinters()
        await loadDefaultPrinter()
    } catch (error) {
        console.error('Failed to set default printer:', error)
        showToast('Ошибка установки принтера по умолчанию', 'error')
    }
}

const deletePrinter = async (printer) => {
    if (!confirm(`Удалить принтер "${printer.name}"?`)) return

    try {
        await axios.delete(`/api/printers/${printer.id}`)
        showToast('Принтер удален', 'success')
        loadPrinters()
    } catch (error) {
        console.error('Failed to delete printer:', error)
        showToast('Ошибка удаления принтера', 'error')
    }
}

const formatDate = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('ru-RU')
}
</script>

<style scoped>
.printers-view {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
}

.section-header {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #f0f0f0;
}

.section-header h1 {
    color: #333;
    font-size: 1.8rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.section-header p {
    color: #666;
    margin: 0;
}

.browser-print-section {
    margin-bottom: 3rem;
}

.browser-print-card {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border: 2px solid #dee2e6;
    border-radius: 12px;
    padding: 2rem;
}

.browser-print-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.browser-print-icon {
    font-size: 3rem;
}

.browser-print-header h3 {
    color: #333;
    margin-bottom: 0.5rem;
    font-size: 1.5rem;
}

.browser-print-description {
    color: #666;
    line-height: 1.5;
    margin: 0;
}

.browser-print-info {
    margin: 2rem 0;
    padding: 1.5rem;
    background: white;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.browser-print-info h5 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #333;
}

.browser-print-info ul {
    margin: 1rem 0;
    padding-left: 1.5rem;
}

.browser-print-info li {
    margin-bottom: 0.5rem;
    line-height: 1.5;
}

.browser-print-actions {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin: 2rem 0;
}

.print-settings {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
}

.setting-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.setting-group label {
    font-weight: 500;
    color: #333;
}

.form-select,
.form-input {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    min-width: 150px;
}

.default-printer-info {
    margin-top: 2rem;
    padding: 1.5rem;
    background: white;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.default-printer-info h5 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #333;
}

.printer-details {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #f0f0f0;
}

.detail-row:last-child {
    border-bottom: none;
}

.detail-label {
    font-weight: 500;
    color: #555;
}

.detail-value {
    color: #333;
}

.status-tag {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.85rem;
    font-weight: 500;
    border-radius: 4px;
}

.status-success {
    background: #d4edda;
    color: #155724;
}

.printers-section {
    margin-top: 3rem;
}

.section-subheader {
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #dee2e6;
}

.section-subheader h2 {
    color: #333;
    font-size: 1.5rem;
    margin: 0;
}

.printers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
}

.printer-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid #dee2e6;
}

.printer-header {
    margin-bottom: 1rem;
}

.printer-title {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.printer-title h3 {
    margin: 0;
    color: #333;
    font-size: 1.2rem;
}

.printer-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: 4px;
    white-space: nowrap;
}

.badge-primary {
    background: #007bff;
    color: white;
}

.badge-success {
    background: #28a745;
    color: white;
}

.badge-secondary {
    background: #6c757d;
    color: white;
}

.printer-type {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #666;
}

.type-icon {
    font-size: 1.2rem;
}

.printer-info {
    margin-bottom: 1rem;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
    border-bottom: none;
}

.info-label {
    font-weight: 500;
    color: #555;
}

.info-value {
    color: #333;
    word-break: break-all;
    text-align: right;
}

.printer-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid #f0f0f0;
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

.btn-lg {
    padding: 1rem 1.5rem;
    font-size: 1.1rem;
}

.btn-icon {
    padding: 0.5rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.2s;
}

.btn-icon:hover {
    background: #f0f0f0;
}

.btn-danger {
    color: #dc3545;
}

.btn-danger:hover {
    background: #f8d7da;
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

@media (max-width: 768px) {
    .printers-view {
        padding: 1rem;
    }

    .printers-grid {
        grid-template-columns: 1fr;
    }

    .print-settings {
        flex-direction: column;
    }

    .printer-actions {
        flex-wrap: wrap;
    }
}
</style>