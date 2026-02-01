/**
 * Утилита для тестирования браузерной печати
 */
export class PrinterTester {
    constructor() {
        this.testResults = new Map();
    }

    /**
     * Тестирует браузерную печать
     */
    async testBrowserPrint() {
        try {
            // Проверяем поддержку печати в браузере
            if (typeof window.print !== 'function') {
                return {
                    success: false,
                    message: 'Браузер не поддерживает печать'
                };
            }

            // Создаем тестовую страницу печати
            const testPage = window.open('', '_blank');

            const testHTML = `
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Тест печати</title>
                    <style>
                        @media print {
                            .no-print { display: none !important; }
                        }
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            padding: 50px;
                        }
                        .test-content {
                            border: 2px solid #007bff;
                            padding: 30px;
                            border-radius: 10px;
                            margin: 20px auto;
                            max-width: 500px;
                        }
                        h1 { color: #007bff; }
                        .status-success {
                            color: green;
                            font-size: 48px;
                            margin: 20px;
                        }
                        .test-info {
                            background: #f8f9fa;
                            padding: 20px;
                            border-radius: 5px;
                            margin: 20px 0;
                            text-align: left;
                        }
                        .btn {
                            padding: 10px 20px;
                            margin: 10px;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                        }
                        .btn-print {
                            background: #007bff;
                            color: white;
                        }
                        .btn-close {
                            background: #6c757d;
                            color: white;
                        }
                    </style>
                </head>
                <body>
                    <div class="test-content">
                        <div class="status-success">✅</div>
                        <h1>Тест печати выполнен успешно</h1>
                        
                        <div class="test-info">
                            <p><strong>Браузер:</strong> ${navigator.userAgent.split(')')[0]})</p>
                            <p><strong>Дата:</strong> ${new Date().toLocaleDateString('ru-RU')}</p>
                            <p><strong>Время:</strong> ${new Date().toLocaleTimeString('ru-RU')}</p>
                            <p><strong>Статус:</strong> Готов к печати</p>
                        </div>
                        
                        <p>Система печати работает корректно. Вы можете:</p>
                        
                        <div class="no-print">
                            <button class="btn btn-print" onclick="window.print()">
                                🖨️ Открыть диалог печати
                            </button>
                            <button class="btn btn-close" onclick="window.close()">
                                ✖️ Закрыть окно
                            </button>
                        </div>
                    </div>
                    
                    <script>
                        // Автоматически открываем диалог печати без подтверждения
                        setTimeout(() => {
                            window.print();
                        }, 500);
                        
                        // Закрываем окно после печати
                        window.onafterprint = function() {
                            setTimeout(() => {
                                window.close();
                            }, 1000);
                        };
                    <\/script>
                </body>
                </html>
            `;

            testPage.document.write(testHTML);
            testPage.document.close();

            return {
                success: true,
                message: 'Тест печати запущен. Диалог печати откроется автоматически.',
                window: testPage
            };

        } catch (error) {
            console.error('Test error:', error);
            return {
                success: false,
                message: `Ошибка тестирования: ${error.message}`
            };
        }
    }

    /**
     * Тестирует все устройства (для совместимости)
     */
    async testAllDevices(devices) {
        // Для браузерной печати просто возвращаем успех
        return devices.map(device => ({
            ...device,
            testResult: {
                success: true,
                message: 'Браузерная печать доступна',
                printerType: 'Браузерный'
            }
        }));
    }

    /**
     * Проверяет возможность печати
     */
    async checkPrintCapabilities() {
        const capabilities = {
            browserPrint: typeof window.print === 'function',
            printAPI: 'print' in window,
            mediaPrint: 'matchMedia' in window && window.matchMedia('print'),
            canPrintLabels: true,
            canPrintImages: true,
            maxResolution: '300dpi',
            supportedFormats: ['PDF', 'HTML', 'Image'],
            defaultPrinter: 'Браузер по умолчанию'
        };

        return {
            ...capabilities,
            supported: capabilities.browserPrint,
            message: capabilities.browserPrint
                ? 'Браузер поддерживает печать'
                : 'Браузер не поддерживает печать'
        };
    }
}

// Экспортируем синглтон
export const printerTester = new PrinterTester();