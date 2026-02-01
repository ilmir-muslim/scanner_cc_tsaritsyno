/**
 * Упрощенный сканер для браузерной печати
 */
export class BrowserNetworkScanner {
    constructor() {
        this.scanResults = [];
        this.isScanning = false;
    }

    /**
     * Основной метод сканирования - возвращает только браузерный принтер
     */
    async scanNetwork(onProgress) {
        if (this.isScanning) {
            return this.scanResults;
        }

        this.isScanning = true;

        try {
            console.log('🚀 Используется браузерная печать по умолчанию');

            // Симулируем прогресс для UI
            if (onProgress) {
                for (let i = 0; i <= 100; i += 10) {
                    setTimeout(() => onProgress(i), i * 20);
                }
            }

            // Возвращаем только браузерный принтер
            this.scanResults = [{
                name: 'Браузерная печать',
                type: 'browser',
                status: 'available',
                description: 'Печать через стандартный диалог браузера',
                icon: '🌐'
            }];

            return this.scanResults;

        } catch (error) {
            console.error('❌ Ошибка сканирования:', error);
            return [];
        } finally {
            this.isScanning = false;
        }
    }

    /**
     * Быстрое сканирование
     */
    async quickScan() {
        return [{
            name: 'Браузерная печать',
            type: 'browser',
            status: 'available',
            description: 'Печать через стандартный диалог браузера'
        }];
    }

    /**
     * Получаем информацию о сети браузера
     */
    getNetworkInfo() {
        return {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            online: navigator.onLine,
            printSupported: 'print' in window,
            printApi: 'Print API доступен'
        };
    }

    /**
     * Проверяем поддержку печати в браузере
     */
    async checkPrintSupport() {
        return {
            supported: 'print' in window,
            message: 'Браузер поддерживает печать',
            browser: navigator.userAgent,
            timestamp: new Date().toISOString()
        };
    }
}

// Экспортируем синглтон для удобства
export const networkScanner = new BrowserNetworkScanner();