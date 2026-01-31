<template>
    <div class="printers-view">
        <div class="section-header">
            <h1>Управление принтерами</h1>
            <p>Настройка подключенных принтеров</p>
        </div>

        <!-- Автоматическое сканирование через браузер -->
        <div class="auto-config-section">
            <div class="auto-config-card">
                <div class="auto-config-header">
                    <div class="auto-config-icon">🔍</div>
                    <div>
                        <h3>Сканирование сети через браузер</h3>
                        <p class="auto-config-description">
                            Используйте ваш браузер для поиска сетевых принтеров в локальной сети.
                            <strong>Сканирование выполняется вашим компьютером, а не сервером.</strong>
                        </p>
                    </div>
                </div>

                <div class="auto-config-actions">
                    <button @click="startEnhancedScan" :disabled="scanning"
                        :class="['btn', 'btn-primary', 'btn-lg', scanning ? 'btn-loading' : '']">
                        <span v-if="scanning" class="spinner"></span>
                        {{ scanning ? 'Сканирование...' : '🎯 Умное сканирование' }}
                    </button>

                    <div class="auto-config-buttons">
                        <button @click="showAddPrinterDialog" class="btn btn-primary">
                            ⚙️ Добавить принтер вручную
                        </button>
                        <button @click="quickScan" :disabled="scanning" class="btn btn-outline">
                            ⚡ Быстрое сканирование
                        </button>
                        <button @click="cleanupBogusPrinters" class="btn btn-warning" v-if="hasBogusPrinters">
                            🗑️ Очистить ненастроенные
                        </button>
                    </div>
                </div>

                <!-- Статус сканирования -->
                <div v-if="scanStatus" class="scan-status" :class="`status-${scanStatus.type}`">
                    <div class="status-header">
                        <h4>{{ scanStatus.title }}</h4>
                        <span class="status-time">{{ scanStatus.time }}</span>
                    </div>
                    <p>{{ scanStatus.message }}</p>

                    <!-- Прогресс сканирования -->
                    <div v-if="scanning" class="scan-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" :style="{ width: scanProgress.percent + '%' }"></div>
                        </div>
                        <div class="progress-info">
                            <span>Сканирование подсетей...</span>
                            <span>{{ scanProgress.percent }}%</span>
                        </div>
                    </div>

                    <!-- Результаты сканирования -->
                    <div v-if="scanResults && scanResults.length > 0" class="scan-results">
                        <h5>Найденные устройства:</h5>
                        <div class="results-grid">
                            <div v-for="(result, index) in scanResults" :key="index" class="result-card">
                                <div class="result-header">
                                    <span class="device-status">
                                        {{ getDeviceStatus(result) }}
                                    </span>
                                    <span class="device-icon">
                                        {{ result.testResult?.printerType ? '🖨️' : '🌐' }}
                                    </span>
                                    <div class="device-info">
                                        <h6>{{ result.name || `Устройство ${result.ip}` }}</h6>
                                        <span class="device-ip">{{ result.ip }}:{{ result.port || 9100 }}</span>
                                        <span class="device-type">
                                            {{ result.testResult?.printerType || result.type || 'Сетевое устройство' }}
                                        </span>
                                        <div v-if="result.testResult" class="device-test-result">
                                            <small>{{ result.testResult.message }}</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="result-actions">
                                    <button @click="addDetectedPrinter(result)" class="btn btn-sm btn-success">
                                        ➕ Добавить
                                    </button>
                                    <button @click="testPrinterConnection(result)" class="btn btn-sm btn-info">
                                        🔍 Тест
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div class="results-summary">
                            <button @click="addAllPrinters" class="btn btn-primary">
                                ✅ Добавить все найденные принтеры
                            </button>
                            <button @click="clearResults" class="btn btn-text">
                                ❌ Очистить результаты
                            </button>
                        </div>
                    </div>

                    <!-- Пустые результаты -->
                    <div v-if="scanStatus.type === 'success' && scanResults.length === 0" class="empty-results">
                        <p>😕 Устройства не найдены. Возможные причины:</p>
                        <ul>
                            <li>Принтеры выключены или не подключены к сети</li>
                            <li>Брандмауэр блокирует сканирование</li>
                            <li>Принтеры находятся в другой подсети</li>
                        </ul>
                        <button @click="showAddPrinterDialog" class="btn btn-outline">
                            ➕ Добавить принтер вручную
                        </button>
                    </div>
                </div>

                <!-- Инструкция -->
                <div class="auto-config-info">
                    <h5>💡 Как работает сканирование:</h5>
                    <ul>
                        <li><strong>Сканирует локальную сеть</strong> через ваш браузер</li>
                        <li>Проверяет стандартные порты принтеров: 9100, 80, 631</li>
                        <li>Автоматически определяет подсети вашей сети</li>
                        <li>Не требует установки дополнительного ПО</li>
                    </ul>
                    <div class="warning-note">
                        <strong>⚠️ Важно:</strong> Сканирование выполняется вашим компьютером,
                        поэтому могут быть ограничения из-за настроек сети и браузера.
                    </div>
                </div>

                <!-- Ручное добавление принтера -->
                <div class="manual-config">
                    <h5>📝 Ручное добавление принтера</h5>
                    <div class="manual-form">
                        <div class="form-row">
                            <input v-model="manualPrinter.ip" placeholder="IP адрес (например: 192.168.1.100)"
                                class="form-input" @keyup.enter="addManualPrinter" />
                            <input v-model="manualPrinter.port" placeholder="Порт (по умолчанию: 9100)" type="number"
                                class="form-input" @keyup.enter="addManualPrinter" />
                        </div>
                        <div class="form-row">
                            <input v-model="manualPrinter.name" placeholder="Название принтера" class="form-input"
                                @keyup.enter="addManualPrinter" />
                            <button @click="addManualPrinter" class="btn btn-primary" :disabled="!manualPrinter.ip">
                                Добавить принтер
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Список принтеров -->
        <div class="printers-section">
            <div class="section-subheader">
                <h2>Настроенные принтеры</h2>
                <div class="controls">
                    <button @click="loadPrinters" class="btn btn-outline">
                        🔄 Обновить список
                    </button>
                </div>
            </div>

            <div v-if="printers.length === 0" class="empty-state">
                <div class="empty-icon">🖨️</div>
                <h3>Принтеры не настроены</h3>
                <p>Используйте сканирование сети или добавьте принтер вручную</p>

                <!-- Быстрые действия -->
                <div class="quick-actions">
                    <button @click="startEnhancedScan" class="btn btn-primary">
                        🔍 Сканировать сеть
                    </button>
                    <button @click="showAddPrinterDialog" class="btn btn-success">
                        ➕ Добавить вручную
                    </button>
                </div>
            </div>

            <div v-else class="printers-grid">
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
                                {{ printer.connection_type === 'network' ? '🌐' :
                                    printer.connection_type === 'usb' ? '🔌' :
                                        printer.connection_type === 'bluetooth' ? '📱' : '🌍' }}
                            </span>
                            <span class="type-text">
                                {{ printer.connection_type === 'network' ? 'Сетевой' :
                                    printer.connection_type === 'usb' ? 'USB' :
                                        printer.connection_type === 'bluetooth' ? 'Bluetooth' : 'Браузер' }}
                            </span>
                        </div>
                    </div>

                    <div class="printer-info">
                        <div v-if="printer.ip_address" class="info-row">
                            <span class="info-label">IP адрес:</span>
                            <span class="info-value">{{ printer.ip_address }}</span>
                        </div>
                        <div v-if="printer.port" class="info-row">
                            <span class="info-label">Порт:</span>
                            <span class="info-value">{{ printer.port }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Добавлен:</span>
                            <span class="info-value">{{ formatDate(printer.created_at) }}</span>
                        </div>
                    </div>

                    <div class="printer-actions">
                        <button @click="testPrinter(printer)" class="btn btn-icon" title="Тест печати">
                            🖨️ Тест
                        </button>
                        <button @click="setDefaultPrinter(printer)" :disabled="printer.is_default" class="btn btn-icon"
                            title="Установить по умолчанию">
                            ⭐ По умолчанию
                        </button>
                        <button @click="editPrinter(printer)" class="btn btn-icon" title="Настройки">
                            ⚙️ Настроить
                        </button>
                        <button @click="deletePrinter(printer)" class="btn btn-icon btn-danger" title="Удалить">
                            🗑️ Удалить
                        </button>
                    </div>
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
                            placeholder="Например: Офисный принтер" />
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
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { BrowserNetworkScanner } from '@/utils/browserNetworkScanner'
import { printerTester } from '@/utils/printerTester'

const printers = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const scanning = ref(false)
const scanResults = ref([])

// Toast variables
const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref('info')

// Статус сканирования
const scanStatus = ref(null)
const scanProgress = ref({
    active: false,
    percent: 0
})

// Ручной ввод принтера
const manualPrinter = ref({
    ip: '',
    port: 9100,
    name: ''
})

const printerForm = ref({
    name: '',
    connection_type: 'network',
    ip_address: '',
    port: 9100,
    is_default: false
})

// Инициализация сканера
const scanner = new BrowserNetworkScanner()

// Computed property для проверки болванок
const hasBogusPrinters = computed(() => {
    return printers.value.some(printer =>
        printer.id === 0 ||
        !printer.name ||
        printer.name.includes('Browser') ||
        (printer.connection_type === 'network' && !printer.ip_address)
    )
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

const updateScanStatus = (title, message, type = 'info') => {
    scanStatus.value = {
        title,
        message,
        type,
        time: new Date().toLocaleTimeString('ru-RU')
    }
}

const loadPrinters = async () => {
    try {
        const response = await axios.get('/api/printers/')

        // Убедимся, что это массив
        if (Array.isArray(response.data)) {
            // Фильтруем "болванки" и принтеры без ID
            printers.value = response.data.filter(printer => {
                // Пропускаем принтеры без ID
                if (!printer || typeof printer !== 'object' || !printer.id || printer.id === 0) return false

                // Пропускаем дефолтные браузерные принтеры без настроек
                if (printer.name && printer.name.includes('Browser') && printer.connection_type === 'browser' && !printer.ip_address) {
                    return false
                }

                // Пропускаем сетевые принтеры без IP
                if (printer.connection_type === 'network' && !printer.ip_address) {
                    return false
                }

                return true
            })
        } else {
            console.warn('API вернул не массив:', response.data)
            printers.value = []
        }

        console.log('Загруженные принтеры (после фильтрации):', printers.value)

    } catch (error) {
        console.error('Failed to load printers:', error)

        // Если сервер вернул ошибку, пробуем загрузить из localStorage
        const cachedPrinters = localStorage.getItem('qr_printers_cache')
        if (cachedPrinters) {
            try {
                printers.value = JSON.parse(cachedPrinters)
                console.log('Используем кэшированные принтеры из localStorage')
            } catch (e) {
                printers.value = []
            }
        } else {
            printers.value = []
        }

        showToast('Ошибка загрузки списка принтеров', 'error')
    }
}

// Функция для очистки "болванок" из базы
const cleanupBogusPrinters = async () => {
    if (!confirm('Удалить все ненастроенные (болванки) принтеры из базы данных?')) return

    try {
        // Загружаем все принтеры
        const response = await axios.get('/api/printers/')
        const allPrinters = response.data

        // Находим болванки для удаления
        const printersToDelete = allPrinters.filter(printer => {
            return (
                printer.id === 0 ||
                !printer.name ||
                printer.name.includes('Browser') ||
                (printer.connection_type === 'network' && !printer.ip_address) ||
                printer.name.includes('болванка') ||
                printer.name.includes('dummy')
            )
        })

        // Удаляем каждый принтер
        for (const printer of printersToDelete) {
            try {
                await axios.delete(`/api/printers/${printer.id}`)
                console.log(`Удален принтер: ${printer.name || 'без имени'} (ID: ${printer.id})`)
            } catch (error) {
                console.error(`Ошибка удаления принтера ${printer.id}:`, error)
            }
        }

        if (printersToDelete.length > 0) {
            showToast(`Удалено ${printersToDelete.length} ненастроенных принтеров`, 'success')
        } else {
            showToast('Ненастроенные принтеры не найдены', 'info')
        }

        // Обновляем список
        await loadPrinters()

    } catch (error) {
        console.error('Cleanup error:', error)
        showToast('Ошибка очистки принтеров', 'error')
    }
}

// Улучшенное сканирование сети через браузер
const startEnhancedScan = async () => {
    try {
        scanning.value = true
        scanResults.value = []
        scanProgress.value = { active: true, percent: 0 }

        updateScanStatus('Улучшенное сканирование', 'Ищем только принтеры...', 'info')

        // Запускаем базовое сканирование
        const allDevices = await scanner.scanNetwork((progress) => {
            scanProgress.value.percent = progress
        })

        // Тестируем найденные устройства
        const testedDevices = await printerTester.testAllDevices(allDevices);
        scanResults.value = testedDevices;

        if (scanResults.value.length > 0) {
            updateScanStatus(
                'Сканирование завершено',
                `Найдено ${scanResults.value.length} устройств`,
                'success'
            )
            showToast(`Найдено ${scanResults.value.length} устройств`, 'success')
        } else {
            updateScanStatus(
                'Сканирование завершено',
                'Устройства не найдены. Добавьте принтер вручную.',
                'info'
            )
        }

    } catch (error) {
        console.error('Scan error:', error)
        updateScanStatus('Ошибка', 'Не удалось выполнить сканирование', 'error')
        showToast('Ошибка сканирования сети', 'error')
    } finally {
        scanning.value = false
        scanProgress.value = { active: false, percent: 0 }
    }
}

// Быстрое сканирование
const quickScan = async () => {
    try {
        scanning.value = true
        scanResults.value = []

        updateScanStatus('Быстрое сканирование', 'Проверяем распространенные адреса принтеров...', 'info')

        const results = await scanner.quickScan()
        scanResults.value = results

        if (results.length > 0) {
            updateScanStatus(
                'Быстрое сканирование завершено',
                `Найдено ${results.length} устройств`,
                'success'
            )
        } else {
            updateScanStatus(
                'Быстрое сканирование завершено',
                'Устройства не найдены. Попробуйте полное сканирование.',
                'info'
            )
        }

    } catch (error) {
        console.error('Quick scan error:', error)
        updateScanStatus('Ошибка', 'Ошибка быстрого сканирования', 'error')
    } finally {
        scanning.value = false
    }
}

// Добавление найденного принтера с проверкой
const addDetectedPrinter = async (printerInfo) => {
    // Проверяем корректность IP
    if (!printerInfo.ip ||
        printerInfo.ip === '0.0.0.0' ||
        printerInfo.ip.startsWith('127.') ||
        printerInfo.ip.startsWith('169.254.')) {
        showToast('Некорректный IP адрес', 'warning')
        return
    }

    try {
        const printerName = printerInfo.name || `Принтер ${printerInfo.ip}`

        // Формируем правильный запрос
        const printerData = {
            name: printerName,
            connection_type: 'network',
            is_default: false,
            is_active: true
        };

        // Добавляем IP только если это сетевой принтер
        if (printerInfo.ip && printerInfo.ip !== '0.0.0.0') {
            printerData.ip_address = printerInfo.ip;
            printerData.port = printerInfo.port || 9100;
        }

        console.log('Отправляем данные принтера:', printerData);

        const response = await axios.post('/api/printers/', printerData, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log('Ответ от сервера:', response.data);

        if (response.data && response.data.id) {
            showToast('Принтер успешно добавлен', 'success');
            await loadPrinters();
        } else {
            showToast('Принтер добавлен, но не получен ID', 'warning');
        }

    } catch (error) {
        console.error('Ошибка добавления принтера:', error);

        if (error.response) {
            // Сервер ответил с ошибкой
            console.error('Ответ сервера:', error.response.data);
            console.error('Статус:', error.response.status);

            if (error.response.status === 400) {
                if (error.response.data && error.response.data.detail) {
                    showToast(`Ошибка: ${error.response.data.detail}`, 'error');
                } else {
                    showToast('Принтер с таким именем или IP уже существует', 'error');
                }
            } else if (error.response.status === 422) {
                showToast('Некорректные данные принтера', 'error');
            } else {
                showToast(`Ошибка сервера: ${error.response.status}`, 'error');
            }
        } else if (error.request) {
            // Запрос был сделан, но ответа не получено
            console.error('Нет ответа от сервера:', error.request);
            showToast('Сервер не отвечает. Проверьте подключение.', 'error');
        } else {
            // Ошибка настройки запроса
            console.error('Ошибка настройки запроса:', error.message);
            showToast('Ошибка настройки запроса: ' + error.message, 'error');
        }
    }
}

// Тестирование соединения с принтером
const testPrinterConnection = async (device) => {
    try {
        showToast('Тестируем соединение с принтером...', 'info');

        // Проверяем доступность порта
        const isAvailable = await scanner.testIP(device.ip, [device.port]);

        if (isAvailable.status === 'online') {
            // Проверяем веб-интерфейс
            const webTest = await printerTester.testPrinterWebInterface(device.ip, device.port);

            if (webTest.success) {
                showToast(`✅ Принтер доступен: ${webTest.printerType}`, 'success');
            } else {
                showToast('⚠️ Устройство доступно, но не похоже на принтер', 'warning');
            }
        } else {
            showToast('❌ Устройство недоступно', 'error');
        }
    } catch (error) {
        console.error('Test error:', error);
        showToast('Ошибка тестирования', 'error');
    }
}

// Добавление всех найденных принтеров
const addAllPrinters = async () => {
    try {
        let addedCount = 0
        let skippedCount = 0

        for (const printer of scanResults.value) {
            // Пропускаем некорректные IP
            if (!printer.ip ||
                printer.ip === '0.0.0.0' ||
                printer.ip.startsWith('127.') ||
                printer.ip.startsWith('169.254.')) {
                skippedCount++
                continue
            }

            try {
                await axios.post('/api/printers/', {
                    name: printer.name || `Принтер ${printer.ip}`,
                    connection_type: 'network',
                    ip_address: printer.ip,
                    port: printer.port || 9100,
                    is_default: false,
                    is_active: true
                })
                addedCount++
            } catch (error) {
                console.error(`Error adding printer ${printer.ip}:`, error)
                skippedCount++
            }
        }

        if (addedCount > 0) {
            showToast(`Добавлено ${addedCount} принтеров${skippedCount > 0 ? `, пропущено ${skippedCount}` : ''}`, 'success')
            await loadPrinters()
            clearResults()
        } else {
            showToast('Не удалось добавить ни одного принтера', 'warning')
        }

    } catch (error) {
        console.error('Error adding printers:', error)
        showToast('Ошибка добавления принтеров', 'error')
    }
}

// Очистка результатов
const clearResults = () => {
    scanResults.value = []
    scanStatus.value = null
}

// Ручное добавление принтера
const addManualPrinter = async () => {
    if (!manualPrinter.value.ip) {
        showToast('Введите IP адрес принтера', 'warning')
        return
    }

    // Проверяем IP
    if (manualPrinter.value.ip.startsWith('127.') ||
        manualPrinter.value.ip.startsWith('169.254.') ||
        manualPrinter.value.ip === '0.0.0.0') {
        showToast('Некорректный IP адрес', 'warning')
        return
    }

    try {
        await axios.post('/api/printers/', {
            name: manualPrinter.value.name || `Принтер ${manualPrinter.value.ip}`,
            connection_type: 'network',
            ip_address: manualPrinter.value.ip,
            port: manualPrinter.value.port || 9100,
            is_default: false,
            is_active: true
        })

        showToast('Принтер добавлен', 'success')
        manualPrinter.value = { ip: '', port: 9100, name: '' }
        await loadPrinters()

    } catch (error) {
        console.error('Error adding manual printer:', error)
        if (error.response && error.response.status === 400) {
            showToast('Принтер с таким IP уже существует', 'error')
        } else {
            showToast('Ошибка добавления принтера', 'error')
        }
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
            await axios.put(`/api/printers/${printerForm.value.id}`, printerForm.value)
            showToast('Принтер обновлен', 'success')
        } else {
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
        const response = await axios.post(`/api/printers/test/${printer.id}`)
        showToast(response.data.message, response.data.status === 'success' ? 'success' : 'error')
    } catch (error) {
        console.error('Printer test failed:', error)
        showToast('Ошибка тестирования принтера', 'error')
    }
}

const setDefaultPrinter = async (printer) => {
    try {
        printerForm.value = { ...printer, is_default: true }
        await axios.put(`/api/printers/${printer.id}`, printerForm.value)
        showToast(`Принтер "${printer.name}" установлен по умолчанию`, 'success')
        loadPrinters()
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

const getDeviceStatus = (device) => {
    if (device.testResult) {
        return device.testResult.success ? '✅' : '❌';
    }
    return '❓';
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

/* Auto Configuration Styles */
.auto-config-section {
    margin-bottom: 3rem;
}

.auto-config-card {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border: 2px solid #dee2e6;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 1.5rem;
}

.auto-config-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.auto-config-icon {
    font-size: 3rem;
}

.auto-config-header h3 {
    color: #333;
    margin-bottom: 0.5rem;
    font-size: 1.5rem;
}

.auto-config-description {
    color: #666;
    line-height: 1.5;
    margin: 0;
}

.auto-config-description strong {
    color: #dc3545;
}

.auto-config-actions {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.auto-config-buttons {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.btn-lg {
    padding: 1rem 1.5rem;
    font-size: 1.1rem;
    font-weight: 500;
}

.btn-loading {
    opacity: 0.7;
    cursor: wait;
}

.spinner {
    display: inline-block;
    width: 1rem;
    height: 1rem;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s ease-in-out infinite;
    margin-right: 0.5rem;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Scan Status */
.scan-status {
    margin-top: 2rem;
    padding: 1.5rem;
    border-radius: 8px;
    border-left: 4px solid #007bff;
    background: white;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-info {
    border-left-color: #17a2b8;
    background: #d1ecf1;
}

.status-success {
    border-left-color: #28a745;
    background: #d4edda;
}

.status-warning {
    border-left-color: #ffc107;
    background: #fff3cd;
}

.status-error {
    border-left-color: #dc3545;
    background: #f8d7da;
}

.status-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.status-header h4 {
    margin: 0;
    color: #333;
    font-size: 1.2rem;
}

.status-time {
    color: #666;
    font-size: 0.9rem;
}

.scan-status p {
    margin: 0 0 1rem 0;
    line-height: 1.5;
}

/* Scan Progress */
.scan-progress {
    margin: 1.5rem 0;
}

.progress-bar {
    width: 100%;
    height: 10px;
    background: #e9ecef;
    border-radius: 5px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #007bff, #0056b3);
    transition: width 0.3s ease;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    margin-top: 0.5rem;
    font-size: 0.9rem;
    color: #666;
}

/* Scan Results */
.scan-results {
    margin-top: 1.5rem;
}

.scan-results h5 {
    margin-bottom: 1rem;
    color: #333;
}

.results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.result-card {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.result-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.device-status {
    font-size: 1.2rem;
}

.device-icon {
    font-size: 1.5rem;
}

.device-info {
    flex: 1;
}

.device-info h6 {
    margin: 0 0 0.25rem 0;
    color: #333;
    font-size: 1rem;
}

.device-ip {
    display: block;
    color: #666;
    font-family: monospace;
    font-size: 0.9rem;
}

.device-type {
    display: block;
    color: #6c757d;
    font-size: 0.85rem;
    margin-top: 0.25rem;
}

.device-test-result {
    margin-top: 0.25rem;
    font-size: 0.8rem;
    color: #666;
    font-style: italic;
}

.result-actions {
    display: flex;
    gap: 0.5rem;
}

.btn-sm {
    padding: 0.25rem 0.5rem;
    font-size: 0.85rem;
}

.results-summary {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid #dee2e6;
}

/* Empty Results */
.empty-results {
    margin-top: 1.5rem;
    padding: 1.5rem;
    background: #fff3cd;
    border-radius: 8px;
    border: 1px solid #ffeaa7;
}

.empty-results ul {
    margin: 1rem 0;
    padding-left: 1.5rem;
}

.empty-results li {
    margin-bottom: 0.5rem;
}

/* Auto Config Info */
.auto-config-info {
    margin-top: 2rem;
    padding: 1.5rem;
    background: #e9ecef;
    border-radius: 8px;
}

.auto-config-info h5 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #333;
}

.auto-config-info ul {
    margin: 1rem 0;
    padding-left: 1.5rem;
}

.auto-config-info li {
    margin-bottom: 0.5rem;
    line-height: 1.5;
}

.warning-note {
    margin-top: 1rem;
    padding: 1rem;
    background: #fff3cd;
    border-radius: 6px;
    border: 1px solid #ffeaa7;
}

.warning-note strong {
    color: #856404;
}

/* Manual Config */
.manual-config {
    margin-top: 2rem;
    padding: 1.5rem;
    background: white;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.manual-config h5 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #333;
}

.manual-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.form-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.form-row .form-input {
    flex: 1;
    min-width: 200px;
}

.form-input {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

.form-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

/* Printers Section */
.printers-section {
    margin-top: 3rem;
}

.section-subheader {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #dee2e6;
    flex-wrap: wrap;
    gap: 1rem;
}

.section-subheader h2 {
    color: #333;
    font-size: 1.5rem;
    margin: 0;
}

.controls {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.empty-state {
    text-align: center;
    padding: 3rem;
    background: #f8f9fa;
    border-radius: 8px;
    border: 2px dashed #dee2e6;
}

.empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.empty-state h3 {
    color: #666;
    margin-bottom: 0.5rem;
}

.empty-state p {
    color: #888;
    margin: 0;
}

.quick-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
    justify-content: center;
    flex-wrap: wrap;
}

.quick-actions .btn {
    padding: 0.75rem 1.5rem;
    font-weight: 500;
}

.printers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
    margin-top: 1rem;
}

.printer-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    border: 1px solid #dee2e6;
}

.printer-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.printer-header {
    margin-bottom: 1.5rem;
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
    word-break: break-all;
    text-align: right;
}

.printer-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid #f0f0f0;
    flex-wrap: wrap;
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
    white-space: nowrap;
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

/* Modal Styles */
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

/* Toast */
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

/* Button Styles */
.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    text-decoration: none;
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

.btn-warning {
    background: #ffc107;
    color: black;
}

.btn-warning:hover {
    background: #e0a800;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn:disabled:hover {
    background: inherit;
    color: inherit;
}

/* Responsive */
@media (max-width: 768px) {
    .printers-view {
        padding: 1rem;
    }

    .auto-config-actions {
        flex-direction: column;
    }

    .printers-grid {
        grid-template-columns: 1fr;
    }

    .printer-actions {
        flex-wrap: wrap;
    }

    .section-subheader {
        flex-direction: column;
        align-items: flex-start;
    }

    .controls {
        width: 100%;
    }

    .results-grid {
        grid-template-columns: 1fr;
    }

    .form-row {
        flex-direction: column;
    }

    .form-row .form-input {
        min-width: 100%;
    }
}
</style>