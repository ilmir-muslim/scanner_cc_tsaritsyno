<template>
    <div class="printers-view">
        <div class="section-header">
            <h1>Управление принтерами</h1>
            <p>Настройка подключенных принтеров</p>
        </div>

        <div class="controls">
            <button @click="showAddPrinterDialog" class="btn btn-success">
                ➕ Добавить принтер
            </button>
            <button @click="loadPrinters" class="btn btn-outline">
                🔄 Обновить список
            </button>
        </div>

        <div class="printers-grid">
            <div v-for="printer in printers" :key="printer.id" class="printer-card">
                <div class="printer-header">
                    <h3>{{ printer.name }}</h3>
                    <span v-if="printer.is_default" class="default-badge">По умолчанию</span>
                </div>

                <div class="printer-info">
                    <div class="info-row">
                        <span class="info-label">Тип:</span>
                        <span class="info-value">{{ printer.connection_type }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">IP адрес:</span>
                        <span class="info-value">{{ printer.ip_address || '—' }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Порт:</span>
                        <span class="info-value">{{ printer.port || '—' }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Статус:</span>
                        <span :class="['status-tag', printer.is_active ? 'status-success' : 'status-error']">
                            {{ printer.is_active ? 'Активен' : 'Неактивен' }}
                        </span>
                    </div>
                </div>

                <div class="printer-actions">
                    <button @click="editPrinter(printer)" class="btn-icon" title="Настройки">
                        ⚙️
                    </button>
                    <button @click="testPrinter(printer)" class="btn-icon" title="Тест печати">
                        🖨️
                    </button>
                    <button @click="deletePrinter(printer)" class="btn-icon btn-icon-danger" title="Удалить">
                        🗑️
                    </button>
                </div>
            </div>
        </div>

        <!-- Add/Edit Printer Dialog -->
        <div v-if="dialogVisible" class="modal-overlay" @click="closeDialog">
            <div class="modal-content" @click.stop>
                <div class="modal-header">
                    <h2>{{ isEditing ? 'Редактировать принтер' : 'Добавить принтер' }}</h2>
                    <button @click="closeDialog" class="btn-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="printerName">Название принтера *</label>
                        <input id="printerName" v-model="printerForm.name" class="form-input"
                            placeholder="Введите название" />
                    </div>

                    <div class="form-group">
                        <label for="connectionType">Тип подключения *</label>
                        <select id="connectionType" v-model="printerForm.connection_type" class="form-select">
                            <option value="network">Сетевое (TCP/IP)</option>
                            <option value="usb">USB</option>
                            <option value="bluetooth">Bluetooth</option>
                            <option value="browser">Браузерная печать</option>
                        </select>
                    </div>

                    <div v-if="printerForm.connection_type === 'network'" class="form-group">
                        <label for="ipAddress">IP адрес *</label>
                        <input id="ipAddress" v-model="printerForm.ip_address" class="form-input"
                            placeholder="192.168.1.100" />
                    </div>

                    <div v-if="printerForm.connection_type === 'network'" class="form-group">
                        <label for="port">Порт</label>
                        <input id="port" v-model="printerForm.port" type="number" class="form-input" placeholder="9100"
                            min="1" max="65535" />
                    </div>

                    <div class="form-group checkbox-group">
                        <input id="isDefault" v-model="printerForm.is_default" type="checkbox" class="form-checkbox" />
                        <label for="isDefault">Использовать по умолчанию</label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button @click="closeDialog" class="btn btn-text">Отмена</button>
                    <button @click="savePrinter" class="btn btn-primary">Сохранить</button>
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
const dialogVisible = ref(false)
const isEditing = ref(false)

// Toast variables
const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref('info')

const printerForm = ref({
    name: '',
    connection_type: 'network',
    ip_address: '',
    port: 9100,
    is_default: false
})

onMounted(() => {
    loadPrinters()
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
        printers.value = response.data
    } catch (error) {
        console.error('Failed to load printers:', error)
        showToast('Ошибка загрузки списка принтеров', 'error')
    }
}

const showAddPrinterDialog = () => {
    isEditing.value = false
    printerForm.value = {
        name: '',
        connection_type: 'network',
        ip_address: '',
        port: 9100,
        is_default: false
    }
    dialogVisible.value = true
}

const editPrinter = (printer) => {
    isEditing.value = true
    printerForm.value = { ...printer }
    dialogVisible.value = true
}

const closeDialog = () => {
    dialogVisible.value = false
}

const savePrinter = async () => {
    try {
        if (!printerForm.value.name.trim()) {
            showToast('Введите название принтера', 'warning')
            return
        }

        if (printerForm.value.connection_type === 'network' && !printerForm.value.ip_address) {
            showToast('Введите IP адрес для сетевого принтера', 'warning')
            return
        }

        if (isEditing.value) {
            // Update existing printer
            await axios.put(`/api/printers/${printerForm.value.id}`, printerForm.value)
            showToast('Принтер обновлен', 'success')
        } else {
            // Create new printer
            await axios.post('/api/printers/', printerForm.value)
            showToast('Принтер добавлен', 'success')
        }

        dialogVisible.value = false
        loadPrinters()

    } catch (error) {
        console.error('Failed to save printer:', error)
        showToast('Ошибка сохранения принтера', 'error')
    }
}

const testPrinter = async (printer) => {
    try {
        await axios.post(`/api/printers/test/${printer.id}`)
        showToast('Тестовое задание отправлено на принтер', 'success')
    } catch (error) {
        console.error('Printer test failed:', error)
        showToast('Ошибка тестирования принтера', 'error')
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
</script>

<style scoped>
.printers-view {
    max-width: 1200px;
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

.controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
}

.printers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-top: 1rem;
}

.printer-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.printer-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.printer-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
}

.printer-header h3 {
    margin: 0;
    color: #333;
    font-size: 1.2rem;
}

.default-badge {
    background: #007bff;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
}

.printer-info {
    margin-bottom: 1.5rem;
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

.status-error {
    background: #f8d7da;
    color: #721c24;
}

.printer-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid #f0f0f0;
}

.btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0.5rem;
    border-radius: 4px;
    transition: background 0.2s;
}

.btn-icon:hover {
    background: #f0f0f0;
}

.btn-icon-danger:hover {
    background: #f8d7da;
    color: #721c24;
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    border-radius: 8px;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #dee2e6;
}

.modal-header h2 {
    margin: 0;
    color: #333;
}

.btn-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #666;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.btn-close:hover {
    color: #333;
}

.modal-body {
    padding: 1.5rem;
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #333;
}

.form-input,
.form-select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.checkbox-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.form-checkbox {
    width: 1.2rem;
    height: 1.2rem;
}

.modal-footer {
    padding: 1.5rem;
    border-top: 1px solid #dee2e6;
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
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

.btn-success {
    background: #28a745;
    color: white;
}

.btn-success:hover {
    background: #1e7e34;
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
</style>