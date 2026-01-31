<template>
    <div class="history-view">
        <div class="section-header">
            <h1>История сканирований</h1>
        </div>

        <div class="controls">
            <div class="filters">
                <input type="date" v-model="filters.startDate" class="filter-input" />
                <input type="date" v-model="filters.endDate" class="filter-input" />
                <button @click="loadHistory" class="btn btn-primary">
                    Применить фильтры
                </button>
            </div>

            <button @click="exportToExcel" class="btn btn-success" :disabled="exporting">
                📊 Экспорт в Excel
            </button>
        </div>

        <div class="history-table">
            <table v-if="scanHistory.length > 0">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>QR Содержимое</th>
                        <th>Источник</th>
                        <th>Время</th>
                        <th>Статус</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="scan in scanHistory" :key="scan.id">
                        <td>{{ scan.id }}</td>
                        <td class="qr-content-cell">
                            <span class="qr-preview-small">
                                <img v-if="scan.qr_image" :src="scan.qr_image" alt="QR" class="qr-small" />
                            </span>
                            <span class="qr-text">{{ truncateText(scan.qr_content, 30) }}</span>
                        </td>
                        <td>{{ scan.scan_source }}</td>
                        <td>{{ formatDateTime(scan.scanned_at) }}</td>
                        <td>
                            <span :class="['status-tag', getStatusClass(scan.print_status)]">
                                {{ scan.print_status }}
                            </span>
                        </td>
                        <td class="actions">
                            <button @click="viewDetails(scan)" class="btn-icon" title="Просмотр деталей">
                                👁️
                            </button>
                            <button @click="reprint(scan.qr_content)" class="btn-icon" title="Печатать снова">
                                🖨️
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
            <div v-else class="empty-state">
                <p>Нет данных для отображения</p>
            </div>
        </div>

        <!-- Details Modal -->
        <div v-if="detailsVisible" class="modal-overlay" @click="closeDetails">
            <div class="modal-content" @click.stop>
                <div class="modal-header">
                    <h2>Детали сканирования</h2>
                    <button @click="closeDetails" class="btn-close">&times;</button>
                </div>
                <div v-if="selectedScan" class="modal-body">
                    <div class="qr-preview-large">
                        <img v-if="selectedScan.qr_image" :src="selectedScan.qr_image" alt="QR Code" class="qr-large" />
                    </div>
                    <div class="details-list">
                        <p><strong>Содержимое:</strong> {{ selectedScan.qr_content }}</p>
                        <p><strong>Источник:</strong> {{ selectedScan.scan_source }}</p>
                        <p><strong>Время сканирования:</strong> {{ formatDateTime(selectedScan.scanned_at) }}</p>
                        <p><strong>Время печати:</strong>
                            {{ selectedScan.printed_at ? formatDateTime(selectedScan.printed_at) : 'Не распечатано' }}
                        </p>
                        <p><strong>Статус:</strong>
                            <span :class="['status-tag', getStatusClass(selectedScan.print_status)]">
                                {{ selectedScan.print_status }}
                            </span>
                        </p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button @click="closeDetails" class="btn btn-text">Закрыть</button>
                    <button @click="reprint(selectedScan.qr_content)" class="btn btn-primary">
                        Печатать
                    </button>
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

const scanHistory = ref([])
const loading = ref(false)
const exporting = ref(false)
const detailsVisible = ref(false)
const selectedScan = ref(null)

// Toast variables
const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref('info')

const filters = ref({
    startDate: '',
    endDate: ''
})

onMounted(() => {
    loadHistory()
})

const showToast = (message, type = 'info') => {
    toastMessage.value = message
    toastType.value = type
    toastVisible.value = true
    setTimeout(() => {
        toastVisible.value = false
    }, 3000)
}

const loadHistory = async () => {
    try {
        loading.value = true
        const params = {}

        if (filters.value.startDate) {
            params.start_date = filters.value.startDate
        }
        if (filters.value.endDate) {
            params.end_date = filters.value.endDate
        }

        const response = await axios.get('/api/scans/', { params })
        scanHistory.value = response.data
    } catch (error) {
        console.error('Failed to load history:', error)
        showToast('Ошибка загрузки истории', 'error')
    } finally {
        loading.value = false
    }
}

const exportToExcel = async () => {
    try {
        exporting.value = true

        const params = {}
        if (filters.value.startDate) {
            params.start_date = filters.value.startDate
        }
        if (filters.value.endDate) {
            params.end_date = filters.value.endDate
        }

        const response = await axios.post('/api/scans/export/', params, {
            responseType: 'blob'
        })

        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `scan_report_${new Date().toISOString().slice(0, 10)}.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()

        showToast('Отчет успешно экспортирован', 'success')
    } catch (error) {
        console.error('Export error:', error)
        showToast('Ошибка экспорта отчета', 'error')
    } finally {
        exporting.value = false
    }
}

const viewDetails = (scan) => {
    selectedScan.value = scan
    detailsVisible.value = true
}

const closeDetails = () => {
    detailsVisible.value = false
    selectedScan.value = null
}

const reprint = (qrContent) => {
    showToast('Функция повторной печати в разработке', 'info')
}

const formatDateTime = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleString('ru-RU')
}

const truncateText = (text, maxLength) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
}

const getStatusClass = (status) => {
    const map = {
        'success': 'status-success',
        'pending': 'status-warning',
        'failed': 'status-error'
    }
    return map[status] || 'status-info'
}
</script>

<style scoped>
.history-view {
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
}

.controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
}

.filters {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
}

.filter-input {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.history-table {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

table {
    width: 100%;
    border-collapse: collapse;
}

thead {
    background: #f8f9fa;
}

th {
    padding: 1rem;
    text-align: left;
    font-weight: 600;
    color: #333;
    border-bottom: 2px solid #dee2e6;
}

td {
    padding: 1rem;
    border-bottom: 1px solid #dee2e6;
}

tbody tr:hover {
    background: #f8f9fa;
}

.qr-content-cell {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.qr-small {
    width: 30px;
    height: 30px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.qr-text {
    word-break: break-all;
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

.status-warning {
    background: #fff3cd;
    color: #856404;
}

.status-error {
    background: #f8d7da;
    color: #721c24;
}

.status-info {
    background: #d1ecf1;
    color: #0c5460;
}

.actions {
    display: flex;
    gap: 0.5rem;
}

.btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0.25rem;
    border-radius: 4px;
    transition: background 0.2s;
}

.btn-icon:hover {
    background: #f0f0f0;
}

.empty-state {
    padding: 3rem;
    text-align: center;
    color: #666;
    background: white;
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
    max-width: 600px;
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

.qr-preview-large {
    display: flex;
    justify-content: center;
    margin-bottom: 1.5rem;
}

.qr-large {
    width: 200px;
    height: 200px;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 8px;
    background: white;
}

.details-list p {
    margin: 0.75rem 0;
    line-height: 1.5;
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