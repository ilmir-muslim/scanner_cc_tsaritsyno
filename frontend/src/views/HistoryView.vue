<template>
    <div class="history-view">
        <div class="section-header">
            <h1>История сканирований</h1>
            <p>Просмотр и управление историей отсканированных QR-кодов</p>
        </div>

        <!-- Фильтры -->
        <div class="filters-section">
            <div class="filters-row">
                <div class="filter-group">
                    <label>Дата с:</label>
                    <input type="date" v-model="filters.startDate" class="filter-input" />
                </div>

                <div class="filter-group">
                    <label>Дата по:</label>
                    <input type="date" v-model="filters.endDate" class="filter-input" />
                </div>

                <div class="filter-group">
                    <label>Источник:</label>
                    <select v-model="filters.source" class="filter-select">
                        <option value="">Все источники</option>
                        <option value="scanner">Сканер</option>
                        <option value="camera">Камера</option>
                    </select>
                </div>

                <div class="filter-group">
                    <label>Статус:</label>
                    <select v-model="filters.status" class="filter-select">
                        <option value="">Все статусы</option>
                        <option value="success">Успешно</option>
                        <option value="pending">В ожидании</option>
                        <option value="failed">Ошибка</option>
                    </select>
                </div>

                <div class="filter-actions">
                    <button @click="applyFilters" class="btn btn-primary">
                        Применить фильтры
                    </button>
                    <button @click="clearFilters" class="btn btn-outline">
                        Сбросить
                    </button>
                </div>
            </div>
        </div>

        <!-- Статистика -->
        <div class="stats-section">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-info">
                        <div class="stat-value">{{ totalScans }}</div>
                        <div class="stat-label">Всего сканов</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-info">
                        <div class="stat-value">{{ successScans }}</div>
                        <div class="stat-label">Успешно напечатано</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-info">
                        <div class="stat-value">{{ pendingScans }}</div>
                        <div class="stat-label">В ожидании</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">❌</div>
                    <div class="stat-info">
                        <div class="stat-value">{{ failedScans }}</div>
                        <div class="stat-label">Ошибки печати</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Таблица истории -->
        <div class="history-table-section">
            <div class="table-header">
                <h3>Записи сканирований</h3>
                <div class="table-actions">
                    <button @click="exportToExcel" class="btn btn-outline">
                        📊 Экспорт в Excel
                    </button>
                    <button @click="refreshHistory" class="btn btn-secondary">
                        🔄 Обновить
                    </button>
                </div>
            </div>

            <div class="table-container">
                <div v-if="loading" class="loading-state">
                    Загрузка данных...
                </div>

                <div v-else-if="filteredHistory.length === 0" class="empty-state">
                    <div class="empty-icon">📭</div>
                    <h3>Нет данных для отображения</h3>
                    <p>Измените фильтры или отсканируйте QR-код</p>
                </div>

                <div v-else class="history-table">
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>QR-код</th>
                                    <th>Источник</th>
                                    <th>Время сканирования</th>
                                    <th>Время печати</th>
                                    <th>Статус</th>
                                    <th>Действия</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="scan in paginatedHistory" :key="scan.id">
                                    <td class="scan-id">{{ scan.id }}</td>
                                    <td class="scan-content">
                                        <div class="qr-preview-small">
                                            <img v-if="scan.qr_image" :src="scan.qr_image" alt="QR" class="qr-small" />
                                            <div v-else class="qr-placeholder">QR</div>
                                        </div>
                                        <div class="content-text">
                                            {{ truncateText(scan.qr_content, 40) }}
                                            <small class="content-full" v-if="scan.qr_content.length > 40"
                                                :title="scan.qr_content">
                                                {{ scan.qr_content }}
                                            </small>
                                        </div>
                                    </td>
                                    <td class="scan-source">
                                        <span
                                            :class="['source-badge', scan.scan_source === 'scanner' ? 'badge-info' : 'badge-warning']">
                                            {{ getSourceName(scan.scan_source) }}
                                        </span>
                                    </td>
                                    <td class="scan-time">{{ formatDateTime(scan.scanned_at) }}</td>
                                    <td class="print-time">
                                        {{ scan.printed_at ? formatDateTime(scan.printed_at) : '—' }}
                                    </td>
                                    <td class="scan-status">
                                        <span :class="['status-badge', getStatusClass(scan.print_status)]">
                                            {{ getStatusText(scan.print_status) }}
                                        </span>
                                    </td>
                                    <td class="scan-actions">
                                        <button @click="viewDetails(scan)" class="btn-icon" title="Просмотр деталей">
                                            👁️
                                        </button>
                                        <button @click="reprint(scan)" class="btn-icon" title="Повторная печать">
                                            🖨️
                                        </button>
                                        <button @click="copyToClipboard(scan.qr_content)" class="btn-icon"
                                            title="Копировать код">
                                            📋
                                        </button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Пагинация -->
                    <div class="pagination" v-if="totalPages > 1">
                        <button @click="prevPage" :disabled="currentPage === 1" class="pagination-btn">
                            ← Назад
                        </button>

                        <div class="page-numbers">
                            <span class="pagination-info">
                                Страница {{ currentPage }} из {{ totalPages }}
                            </span>
                            <span class="pagination-info">
                                Показано {{ startItem }}-{{ endItem }} из {{ filteredHistory.length }}
                            </span>
                        </div>

                        <button @click="nextPage" :disabled="currentPage === totalPages" class="pagination-btn">
                            Вперед →
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Модальное окно деталей -->
        <div v-if="showDetailsModal" class="modal-overlay" @click.self="closeDetailsModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Детали сканирования #{{ selectedScan?.id }}</h2>
                    <button @click="closeDetailsModal" class="modal-close">&times;</button>
                </div>

                <div v-if="selectedScan" class="modal-body">
                    <div class="details-grid">
                        <div class="qr-preview-large">
                            <div class="qr-title">QR-код:</div>
                            <img v-if="selectedScan.qr_image" :src="selectedScan.qr_image" alt="QR Code"
                                class="qr-large" />
                            <div v-else class="qr-placeholder-large">
                                <span>QR-код не сгенерирован</span>
                            </div>
                        </div>

                        <div class="details-info">
                            <div class="detail-item">
                                <span class="detail-label">Содержимое QR-кода:</span>
                                <pre class="detail-value">{{ selectedScan.qr_content }}</pre>
                            </div>

                            <div class="detail-row">
                                <div class="detail-item">
                                    <span class="detail-label">Источник сканирования:</span>
                                    <span class="detail-value">{{ getSourceName(selectedScan.scan_source) }}</span>
                                </div>

                                <div class="detail-item">
                                    <span class="detail-label">Статус печати:</span>
                                    <span :class="['detail-value', getStatusClass(selectedScan.print_status)]">
                                        {{ getStatusText(selectedScan.print_status) }}
                                    </span>
                                </div>
                            </div>

                            <div class="detail-row">
                                <div class="detail-item">
                                    <span class="detail-label">Время сканирования:</span>
                                    <span class="detail-value">{{ formatDateTime(selectedScan.scanned_at) }}</span>
                                </div>

                                <div class="detail-item">
                                    <span class="detail-label">Время печати:</span>
                                    <span class="detail-value">
                                        {{ selectedScan.printed_at ? formatDateTime(selectedScan.printed_at) : 'Не напечатано' }}
                                    </span>
                                </div>
                            </div>

                            <div class="detail-item">
                                <span class="detail-label">ID записи:</span>
                                <span class="detail-value">{{ selectedScan.id }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="modal-footer">
                    <button @click="closeDetailsModal" class="btn btn-text">Закрыть</button>
                    <button @click="reprint(selectedScan)" class="btn btn-primary">
                        🖨️ Повторная печать
                    </button>
                    <button @click="copyToClipboard(selectedScan?.qr_content)" class="btn btn-secondary">
                        📋 Копировать код
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const history = ref([])
const loading = ref(false)
const currentPage = ref(1)
const itemsPerPage = 10
const showDetailsModal = ref(false)
const selectedScan = ref(null)

const filters = ref({
    startDate: '',
    endDate: '',
    source: '',
    status: ''
})

onMounted(() => {
    loadHistory()
})

const loadHistory = async () => {
    loading.value = true
    try {
        const response = await axios.get('/api/scans/')
        history.value = response.data
    } catch (error) {
        console.error('Failed to load history:', error)
        // Заглушка для демонстрации
        history.value = generateMockData()
    } finally {
        loading.value = false
    }
}

const refreshHistory = () => {
    loadHistory()
}

const applyFilters = () => {
    currentPage.value = 1
}

const clearFilters = () => {
    filters.value = {
        startDate: '',
        endDate: '',
        source: '',
        status: ''
    }
    currentPage.value = 1
}

const filteredHistory = computed(() => {
    let filtered = [...history.value]

    if (filters.value.startDate) {
        const startDate = new Date(filters.value.startDate)
        filtered = filtered.filter(scan => new Date(scan.scanned_at) >= startDate)
    }

    if (filters.value.endDate) {
        const endDate = new Date(filters.value.endDate)
        endDate.setHours(23, 59, 59, 999)
        filtered = filtered.filter(scan => new Date(scan.scanned_at) <= endDate)
    }

    if (filters.value.source) {
        filtered = filtered.filter(scan => scan.scan_source === filters.value.source)
    }

    if (filters.value.status) {
        filtered = filtered.filter(scan => scan.print_status === filters.value.status)
    }

    return filtered.sort((a, b) => new Date(b.scanned_at) - new Date(a.scanned_at))
})

const paginatedHistory = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage
    const end = start + itemsPerPage
    return filteredHistory.value.slice(start, end)
})

const totalPages = computed(() => {
    return Math.ceil(filteredHistory.value.length / itemsPerPage)
})

const startItem = computed(() => {
    return (currentPage.value - 1) * itemsPerPage + 1
})

const endItem = computed(() => {
    return Math.min(currentPage.value * itemsPerPage, filteredHistory.value.length)
})

const totalScans = computed(() => history.value.length)
const successScans = computed(() => history.value.filter(s => s.print_status === 'success').length)
const pendingScans = computed(() => history.value.filter(s => s.print_status === 'pending').length)
const failedScans = computed(() => history.value.filter(s => s.print_status === 'failed').length)

const prevPage = () => {
    if (currentPage.value > 1) {
        currentPage.value--
    }
}

const nextPage = () => {
    if (currentPage.value < totalPages.value) {
        currentPage.value++
    }
}

const viewDetails = (scan) => {
    selectedScan.value = scan
    showDetailsModal.value = true
}

const closeDetailsModal = () => {
    showDetailsModal.value = false
    selectedScan.value = null
}

const reprint = (scan) => {
    const printWindow = window.open('', '_blank')

    const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Повторная печать QR-кода</title>
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
                .qr-header {
                    font-weight: bold;
                    margin-bottom: 3mm;
                    font-size: 12pt;
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
                <div class="qr-header">ПОВТОРНАЯ ПЕЧАТЬ</div>
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(scan.qr_content)}" 
                     alt="QR Code" class="qr-image" />
                <div class="qr-content">
                    ${scan.qr_content}
                </div>
                <div class="print-info">
                    ID: ${scan.id}<br>
                    Первоначальное сканирование: ${new Date(scan.scanned_at).toLocaleString('ru-RU')}<br>
                    Повторная печать: ${new Date().toLocaleString('ru-RU')}
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
}

const exportToExcel = async () => {
    try {
        const params = {}
        if (filters.value.startDate) params.start_date = filters.value.startDate
        if (filters.value.endDate) params.end_date = filters.value.endDate

        const response = await axios.post('/api/scans/export/', params, {
            responseType: 'blob'
        })

        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `scan_history_${new Date().toISOString().slice(0, 10)}.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()

    } catch (error) {
        console.error('Export error:', error)
        alert('Ошибка экспорта данных')
    }
}

const copyToClipboard = async (text) => {
    try {
        await navigator.clipboard.writeText(text)
        alert('Код скопирован в буфер обмена')
    } catch (error) {
        console.error('Copy error:', error)
        alert('Ошибка копирования')
    }
}

const truncateText = (text, maxLength) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
}

const formatDateTime = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}

const getSourceName = (source) => {
    const sources = {
        'scanner': 'Сканер',
        'camera': 'Камера'
    }
    return sources[source] || source
}

const getStatusClass = (status) => {
    const map = {
        'success': 'status-success',
        'pending': 'status-warning',
        'failed': 'status-error'
    }
    return map[status] || 'status-info'
}

const getStatusText = (status) => {
    const map = {
        'success': 'Успешно',
        'pending': 'В ожидании',
        'failed': 'Ошибка'
    }
    return map[status] || status
}

// Функция для генерации тестовых данных (если API не работает)
const generateMockData = () => {
    const mockData = []
    const sources = ['scanner', 'camera']
    const statuses = ['success', 'pending', 'failed']

    for (let i = 1; i <= 50; i++) {
        const date = new Date()
        date.setDate(date.getDate() - Math.floor(Math.random() * 30))
        date.setHours(Math.floor(Math.random() * 24))
        date.setMinutes(Math.floor(Math.random() * 60))

        const content = `QR-CODE-${1000 + i}-TEST-${Date.now().toString(36)}`
        const source = sources[Math.floor(Math.random() * sources.length)]
        const status = statuses[Math.floor(Math.random() * statuses.length)]

        mockData.push({
            id: i,
            qr_content: content,
            scan_source: source,
            scanned_at: date.toISOString(),
            printed_at: status === 'success' ? new Date(date.getTime() + 10000).toISOString() : null,
            print_status: status,
            qr_image: `https://api.qrserver.com/v1/create-qr-code/?size=50x50&data=${encodeURIComponent(content)}`
        })
    }

    return mockData
}
</script>

<style scoped>
.history-view {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem;
}

.section-header {
    margin-bottom: 2rem;
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

/* Фильтры */
.filters-section {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filters-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: flex-end;
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 150px;
}

.filter-group label {
    font-weight: 500;
    color: #333;
    font-size: 0.9rem;
}

.filter-input,
.filter-select {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.9rem;
}

.filter-actions {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
}

/* Статистика */
.stats-section {
    margin-bottom: 2rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.stat-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-icon {
    font-size: 2rem;
    opacity: 0.7;
}

.stat-info {
    flex: 1;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: #333;
    line-height: 1;
}

.stat-label {
    font-size: 0.9rem;
    color: #666;
    margin-top: 0.25rem;
}

/* Таблица */
.history-table-section {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #eee;
    flex-wrap: wrap;
    gap: 1rem;
}

.table-header h3 {
    color: #333;
    font-size: 1.2rem;
    margin: 0;
}

.table-actions {
    display: flex;
    gap: 0.5rem;
}

.table-container {
    padding: 0;
}

.loading-state {
    padding: 3rem;
    text-align: center;
    color: #666;
    font-style: italic;
}

.empty-state {
    padding: 3rem;
    text-align: center;
    color: #666;
}

.empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.empty-state h3 {
    margin: 0 0 0.5rem 0;
    color: #333;
}

.empty-state p {
    margin: 0;
    color: #666;
}

.table-responsive {
    overflow-x: auto;
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
    white-space: nowrap;
}

td {
    padding: 1rem;
    border-bottom: 1px solid #eee;
    vertical-align: middle;
}

tbody tr:hover {
    background: #f8f9fa;
}

/* Стили для ячеек */
.scan-id {
    font-family: monospace;
    color: #666;
    font-size: 0.9rem;
}

.scan-content {
    min-width: 300px;
}

.qr-preview-small {
    display: inline-block;
    vertical-align: middle;
    margin-right: 0.5rem;
}

.qr-small {
    width: 40px;
    height: 40px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.qr-placeholder {
    width: 40px;
    height: 40px;
    border: 1px dashed #ddd;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    color: #999;
}

.content-text {
    display: inline-block;
    vertical-align: middle;
    max-width: 250px;
}

.content-full {
    display: none;
    position: absolute;
    background: white;
    border: 1px solid #ddd;
    padding: 0.5rem;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    z-index: 100;
    max-width: 400px;
    word-break: break-all;
}

.content-text:hover .content-full {
    display: block;
}

.scan-source {
    white-space: nowrap;
}

.source-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.85rem;
    border-radius: 4px;
}

.badge-info {
    background: #d1ecf1;
    color: #0c5460;
}

.badge-warning {
    background: #fff3cd;
    color: #856404;
}

.scan-time,
.print-time {
    white-space: nowrap;
    font-size: 0.9rem;
    color: #666;
}

.scan-status {
    white-space: nowrap;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.85rem;
    border-radius: 4px;
    min-width: 80px;
    text-align: center;
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

.scan-actions {
    white-space: nowrap;
}

.btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0.25rem;
    border-radius: 4px;
    transition: background 0.2s;
    margin: 0 0.125rem;
}

.btn-icon:hover {
    background: #f0f0f0;
}

/* Пагинация */
.pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-top: 1px solid #eee;
    flex-wrap: wrap;
    gap: 1rem;
}

.pagination-btn {
    padding: 0.5rem 1rem;
    border: 1px solid #ddd;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.pagination-btn:hover:not(:disabled) {
    background: #f8f9fa;
}

.pagination-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.page-numbers {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
}

.pagination-info {
    font-size: 0.9rem;
    color: #666;
}

/* Модальное окно */
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
    padding: 1rem;
}

.modal-content {
    background: white;
    border-radius: 8px;
    width: 90%;
    max-width: 800px;
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
    font-size: 1.5rem;
}

.modal-close {
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

.modal-close:hover {
    color: #333;
}

.modal-body {
    padding: 1.5rem;
}

.details-grid {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 2rem;
}

.qr-preview-large {
    text-align: center;
}

.qr-title {
    font-weight: 600;
    margin-bottom: 1rem;
    color: #333;
}

.qr-large {
    width: 180px;
    height: 180px;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 8px;
    background: white;
}

.qr-placeholder-large {
    width: 180px;
    height: 180px;
    border: 2px dashed #ddd;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #999;
}

.details-info {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.detail-item {
    margin-bottom: 1rem;
}

.detail-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

.detail-label {
    display: block;
    font-weight: 600;
    color: #555;
    margin-bottom: 0.25rem;
    font-size: 0.9rem;
}

.detail-value {
    display: block;
    color: #333;
    word-break: break-all;
}

.detail-value pre {
    margin: 0;
    white-space: pre-wrap;
    font-family: monospace;
    background: #f8f9fa;
    padding: 0.75rem;
    border-radius: 4px;
    font-size: 0.9rem;
    max-height: 200px;
    overflow-y: auto;
}

.modal-footer {
    padding: 1.5rem;
    border-top: 1px solid #dee2e6;
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
}

/* Кнопки */
.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
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

@media (max-width: 768px) {
    .history-view {
        padding: 0.5rem;
    }

    .filters-row {
        flex-direction: column;
        align-items: stretch;
    }

    .filter-group {
        min-width: auto;
    }

    .filter-actions {
        margin-left: 0;
        justify-content: center;
    }

    .stats-grid {
        grid-template-columns: 1fr;
    }

    .table-header {
        flex-direction: column;
        align-items: stretch;
    }

    .table-actions {
        justify-content: center;
    }

    th,
    td {
        padding: 0.5rem;
        font-size: 0.9rem;
    }

    .details-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }

    .detail-row {
        grid-template-columns: 1fr;
        gap: 0.5rem;
    }

    .modal-footer {
        flex-direction: column;
    }

    .modal-footer .btn {
        width: 100%;
    }
}
</style>