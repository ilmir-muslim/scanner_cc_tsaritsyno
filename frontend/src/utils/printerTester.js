/**
 * Утилита для тестирования принтеров через веб-интерфейс
 */
export class PrinterTester {
    constructor() {
        this.testResults = new Map();
    }

    /**
     * Проверяет, поддерживает ли принтер HTTP-печать
     */
    async testPrinterWebInterface(ip, port = 80) {
        try {
            const testUrls = [
                `http://${ip}:${port}/`,
                `http://${ip}:${port}/index.html`,
                `http://${ip}:${port}/status`,
                `http://${ip}:${port}/printer`,
            ];

            for (const url of testUrls) {
                try {
                    const response = await fetch(url, {
                        method: 'GET',
                        mode: 'no-cors',
                        headers: {
                            'Accept': 'text/html,application/xhtml+xml,application/xml'
                        }
                    });

                    // Для no-cors mode response.type будет 'opaque'
                    if (response.type !== 'error') {
                        // Пробуем определить тип принтера по URL
                        const printerType = this.detectPrinterTypeByUrl(url);

                        return {
                            success: true,
                            ip,
                            port,
                            webInterface: url,
                            printerType,
                            message: `Веб-интерфейс найден: ${printerType}`
                        };
                    }
                } catch (error) {
                    continue;
                }
            }

            return {
                success: false,
                ip,
                port,
                message: 'Веб-интерфейс не найден'
            };

        } catch (error) {
            return {
                success: false,
                ip,
                port,
                message: `Ошибка тестирования: ${error.message}`
            };
        }
    }

    /**
     * Определяет тип принтера по URL
     */
    detectPrinterTypeByUrl(url) {
        const urlLower = url.toLowerCase();

        // Список известных принтеров и их ключевых слов
        const printerPatterns = {
            'HP': ['hp', 'hewlett'],
            'Brother': ['brother'],
            'Canon': ['canon'],
            'Epson': ['epson'],
            'Zebra': ['zebra'],
            'Kyocera': ['kyocera'],
            'Ricoh': ['ricoh'],
            'Xerox': ['xerox'],
            'Lexmark': ['lexmark'],
            'Samsung': ['samsung'],
            'OKI': ['oki'],
            'Konica': ['konica'],
            'Sharp': ['sharp'],
            'Toshiba': ['toshiba'],
        };

        for (const [brand, patterns] of Object.entries(printerPatterns)) {
            for (const pattern of patterns) {
                if (urlLower.includes(pattern)) {
                    return brand;
                }
            }
        }

        return 'Неизвестный принтер';
    }

    /**
     * Тестирует все обнаруженные устройства
     */
    async testAllDevices(devices) {
        const results = [];

        for (const device of devices) {
            if (device.port === 80 || device.port === 443) {
                const result = await this.testPrinterWebInterface(device.ip, device.port);
                results.push({
                    ...device,
                    testResult: result
                });
            } else {
                results.push({
                    ...device,
                    testResult: {
                        success: true,
                        message: 'Порт доступен, требуется дополнительная настройка'
                    }
                });
            }
        }

        return results;
    }

    /**
     * Проверяет возможность печати через веб-интерфейс
     */
    async checkPrintCapabilities(ip, port = 80) {
        const printTestUrls = [
            `http://${ip}:${port}/PRESENTATION/HTML/TOP/PRTTOP.HTML`,
            `http://${ip}:${port}/print`,
            `http://${ip}:${port}/printing`,
            `http://${ip}:${port}/cgi-bin/direct/printer/prtconfig.cgi`,
        ];

        for (const url of printTestUrls) {
            try {
                const response = await fetch(url, {
                    method: 'HEAD',
                    mode: 'no-cors'
                });

                if (response.type !== 'error') {
                    return {
                        canPrint: true,
                        printUrl: url,
                        message: 'Поддерживается веб-печать'
                    };
                }
            } catch (error) {
                continue;
            }
        }

        return {
            canPrint: false,
            message: 'Веб-печать не поддерживается'
        };
    }
}

// Экспортируем синглтон
export const printerTester = new PrinterTester();