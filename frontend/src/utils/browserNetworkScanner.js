/**
 * Браузерный сканер сети для поиска принтеров и устройств
 * Работает полностью в браузере пользователя без серверного участия
 */
export class BrowserNetworkScanner {
    constructor() {
        this.localIPs = [];
        this.scanResults = [];
        this.isScanning = false;
        this.commonSubnets = ['192.168.1', '192.168.0', '10.0.0', '192.168.100'];
        this.printerPorts = [9100, 515, 631, 80, 443, 50000, 9220];
    }

    /**
     * Получаем локальные IP через WebRTC (без диалога подтверждения)
     */
    async getLocalIPs() {
        return new Promise((resolve) => {
            const RTCPeerConnection = window.RTCPeerConnection ||
                window.mozRTCPeerConnection ||
                window.webkitRTCPeerConnection;

            if (!RTCPeerConnection) {
                resolve(this.commonSubnets);
                return;
            }

            const pc = new RTCPeerConnection({ iceServers: [] });
            const ips = [];

            pc.createDataChannel('');
            pc.createOffer()
                .then(offer => pc.setLocalDescription(offer))
                .catch(() => resolve(this.commonSubnets));

            pc.onicecandidate = (event) => {
                if (!event.candidate) {
                    pc.onicecandidate = null;
                    pc.close();
                    if (ips.length > 0) {
                        // Извлекаем подсети из IP
                        const subnets = ips.map(ip => {
                            const parts = ip.split('.');
                            return parts.slice(0, 3).join('.');
                        });
                        resolve([...new Set(subnets)]);
                    } else {
                        resolve(this.commonSubnets);
                    }
                    return;
                }

                const candidate = event.candidate.candidate;
                const match = candidate.match(/([0-9]{1,3}(\.[0-9]{1,3}){3})/);
                if (match) {
                    const ip = match[1];
                    // Фильтруем локальные и публичные IP
                    if (!ips.includes(ip) && !ip.startsWith('127.') && !ip.startsWith('169.254.')) {
                        ips.push(ip);
                    }
                }
            };

            setTimeout(() => {
                pc.onicecandidate = null;
                pc.close();
                resolve(this.commonSubnets);
            }, 1000);
        });
    }

    /**
     * Проверяем доступность порта через Image (работает без CORS)
     */
    checkPortViaImage(ip, port) {
        return new Promise((resolve) => {
            const img = new Image();
            const timeout = setTimeout(() => {
                img.onload = img.onerror = null;
                resolve({ ip, port, status: 'closed' });
            }, 500);

            img.onload = () => {
                clearTimeout(timeout);
                resolve({ ip, port, status: 'open' });
            };

            img.onerror = () => {
                clearTimeout(timeout);
                resolve({ ip, port, status: 'closed' });
            };

            // Пробуем загрузить иконку (многие принтеры имеют веб-интерфейс)
            img.src = `http://${ip}:${port}/favicon.ico`;
            img.crossOrigin = 'anonymous';
        });
    }

    /**
     * Проверяем через fetch с no-cors (только для HTTP/HTTPS)
     */
    async checkPortViaFetch(ip, port) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 500);

            const response = await fetch(`http://${ip}:${port}`, {
                mode: 'no-cors',
                signal: controller.signal,
                method: 'GET',
                headers: {
                    'Accept': '*/*'
                }
            });

            clearTimeout(timeoutId);
            return { ip, port, status: 'open' };
        } catch (error) {
            return { ip, port, status: 'closed' };
        }
    }

    /**
     * Проверяем доступность IP:порта (комбинированный метод)
     */
    async checkPort(ip, port) {
        // Для портов 80 и 443 используем fetch
        if (port === 80 || port === 443) {
            return this.checkPortViaFetch(ip, port);
        }
        // Для остальных портов используем Image
        return this.checkPortViaImage(ip, port);
    }

    /**
     * Определяем тип устройства по порту
     */
    getDeviceType(port) {
        const portMap = {
            9100: 'Zebra/Сетевой принтер',
            515: 'LPR принтер',
            631: 'IPP принтер',
            80: 'Веб-интерфейс устройства',
            443: 'HTTPS устройство',
            50000: 'HP JetDirect принтер',
            9220: 'Brother принтер'
        };
        return portMap[port] || 'Сетевое устройство';
    }

    /**
     * Улучшенная фильтрация принтеров
     */
    filterPrinters(devices) {
        return devices.filter(device => {
            // Исключаем внутренние IP адреса Docker/локальные
            if (device.ip.startsWith('172.') ||
                device.ip.startsWith('192.168.0.') ||
                device.ip.startsWith('10.')) {

                // Проверяем, является ли это принтером
                const isPrinter = this.isLikelyPrinter(device);
                return isPrinter;
            }

            return false;
        });
    }

    /**
     * Определяет, является ли устройство принтером
     */
    isLikelyPrinter(device) {
        // Порты, специфичные для принтеров
        const printerPorts = [9100, 515, 631, 9220, 50000];

        // Если порт специфичен для принтера
        if (printerPorts.includes(device.port)) {
            return true;
        }

        // Для порта 80 - дополнительные проверки
        if (device.port === 80 || device.port === 443) {
            // Проверяем, не является ли это роутером (обычно 192.168.1.1)
            if (device.ip === '192.168.1.1' || device.ip === '192.168.0.1') {
                return false; // Это роутер
            }

            // Проверяем специфичные адреса принтеров
            const lastOctet = parseInt(device.ip.split('.').pop());
            if (lastOctet >= 100 && lastOctet <= 150) {
                return true; // Вероятно принтер
            }
        }

        return false;
    }

    /**
     * Проверяет, является ли веб-интерфейс принтером
     */
    async checkIfPrinterWebInterface(ip) {
        try {
            // Пробуем получить заголовки
            const response = await fetch(`http://${ip}`, {
                method: 'HEAD',
                mode: 'no-cors',
                cache: 'no-cache'
            });

            // Для no-cors mode мы не можем прочитать ответ, но можем проверить
            // Альтернативно, используем изображение для определения
            return await this.detectPrinterByFavicon(ip);
        } catch (error) {
            return false;
        }
    }

    /**
     * Определяет принтер по фавиконке (многие принтеры имеют уникальные иконки)
     */
    async detectPrinterByFavicon(ip) {
        try {
            const img = new Image();

            return new Promise((resolve) => {
                img.onload = () => {
                    // Если изображение загрузилось, проверяем размеры
                    // У принтеров часто небольшие иконки
                    resolve(img.width <= 32 && img.height <= 32);
                };

                img.onerror = () => {
                    resolve(false);
                };

                // Устанавливаем таймаут
                setTimeout(() => resolve(false), 1000);

                img.src = `http://${ip}/favicon.ico`;
            });
        } catch (error) {
            return false;
        }
    }

    /**
     * Сканируем одну подсеть
     */
    async scanSubnet(subnet, ports, onProgress) {
        const results = [];
        const tasks = [];

        // Сканируем только первые 15 адресов для скорости
        for (let i = 1; i <= 15; i++) {
            const ip = `${subnet}.${i}`;

            // Создаем задачи для каждого порта
            for (const port of ports) {
                tasks.push(this.checkPort(ip, port));
            }

            // Обновляем прогресс
            if (onProgress) {
                const progress = Math.round((i / 15) * 100);
                onProgress(progress);
            }
        }

        // Выполняем все проверки параллельно с ограничением
        const chunkSize = 10;
        for (let i = 0; i < tasks.length; i += chunkSize) {
            const chunk = tasks.slice(i, i + chunkSize);
            const chunkResults = await Promise.all(chunk);

            // Обрабатываем результаты
            for (const result of chunkResults) {
                if (result.status === 'open') {
                    // Проверяем, не добавили ли уже этот IP
                    const existing = results.find(r => r.ip === result.ip);
                    if (!existing) {
                        results.push({
                            ip: result.ip,
                            port: result.port,
                            name: `Устройство ${result.ip}:${result.port}`,
                            type: this.getDeviceType(result.port),
                            status: 'online'
                        });
                    }
                }
            }

            // Небольшая задержка между чанками
            await new Promise(resolve => setTimeout(resolve, 50));
        }

        return results;
    }

    /**
     * Основной метод сканирования сети
     */
    async scanNetwork(onProgress) {
        if (this.isScanning) {
            return this.scanResults;
        }

        this.isScanning = true;
        this.scanResults = [];

        try {
            console.log('🚀 Запуск браузерного сканирования сети...');

            // Получаем локальные подсети
            const subnets = await this.getLocalIPs();
            console.log('📡 Определены подсети:', subnets);

            // Добавляем стандартные подсети
            const allSubnets = [...new Set([...subnets, ...this.commonSubnets])];

            let totalProgress = 0;
            const progressPerSubnet = 100 / allSubnets.length;

            // Сканируем каждую подсеть
            for (let i = 0; i < allSubnets.length; i++) {
                const subnet = allSubnets[i];
                console.log(`🔍 Сканирование подсети: ${subnet}.x`);

                try {
                    const subnetProgress = (progress) => {
                        const baseProgress = i * progressPerSubnet;
                        const currentProgress = baseProgress + (progress * progressPerSubnet / 100);
                        totalProgress = Math.min(currentProgress, 100);

                        if (onProgress) {
                            onProgress(Math.round(totalProgress));
                        }
                    };

                    const results = await this.scanSubnet(subnet, this.printerPorts, subnetProgress);
                    this.scanResults.push(...results);

                    console.log(`✅ Подсеть ${subnet}: найдено ${results.length} устройств`);

                } catch (error) {
                    console.warn(`⚠️ Ошибка сканирования подсети ${subnet}:`, error);
                }
            }

            // Проверяем распространённые адреса принтеров
            const commonResults = await this.scanCommonPrinterAddresses();
            this.scanResults.push(...commonResults);

            // Удаляем дубликаты
            this.scanResults = this.removeDuplicates(this.scanResults);

            // Фильтруем только принтеры
            const filteredResults = this.filterPrinters(this.scanResults);
            this.scanResults = filteredResults;

            console.log(`🎉 Сканирование завершено. После фильтрации: ${this.scanResults.length} устройств`);
            return this.scanResults;

        } catch (error) {
            console.error('❌ Критическая ошибка сканирования:', error);
            return [];
        } finally {
            this.isScanning = false;
        }
    }

    /**
     * Сканируем наиболее распространённые адреса принтеров
     */
    async scanCommonPrinterAddresses() {
        const commonIPs = [
            '192.168.1.100', '192.168.1.101', '192.168.1.102',
            '192.168.0.100', '192.168.0.101', '192.168.0.102',
            '10.0.0.100', '10.0.0.101', '10.0.0.102',
            '192.168.1.200', '192.168.0.200', '10.0.0.200',
            '192.168.1.1', '192.168.0.1', '10.0.0.1',
            '192.168.1.254', '192.168.0.254', '10.0.0.254'
        ];

        const results = [];
        const tasks = [];

        for (const ip of commonIPs) {
            for (const port of this.printerPorts) {
                tasks.push(this.checkPort(ip, port));
            }
        }

        const portResults = await Promise.all(tasks);

        for (const result of portResults) {
            if (result.status === 'open') {
                const existing = results.find(r => r.ip === result.ip);
                if (!existing) {
                    results.push({
                        ip: result.ip,
                        port: result.port,
                        name: `Принтер ${result.ip}`,
                        type: this.getDeviceType(result.port),
                        status: 'online'
                    });
                }
            }
        }

        return results;
    }

    /**
     * Быстрое сканирование (только популярные адреса)
     */
    async quickScan() {
        console.log('⚡ Быстрое сканирование популярных адресов...');
        return await this.scanCommonPrinterAddresses();
    }

    /**
     * Удаляем дубликаты устройств
     */
    removeDuplicates(devices) {
        const unique = [];
        const seen = new Set();

        for (const device of devices) {
            const key = `${device.ip}:${device.port}`;
            if (!seen.has(key)) {
                seen.add(key);
                unique.push(device);
            }
        }

        return unique;
    }

    /**
     * Получаем информацию о сети браузера
     */
    getNetworkInfo() {
        const info = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            online: navigator.onLine,
            localIPs: this.localIPs
        };

        // Информация о соединении
        if (navigator.connection) {
            info.connection = {
                type: navigator.connection.type,
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            };
        }

        return info;
    }

    /**
     * Проверяем конкретный IP адрес на доступность
     */
    async testIP(ip, ports = null) {
        if (!ports) {
            ports = this.printerPorts;
        }

        const results = [];
        const tasks = ports.map(port => this.checkPort(ip, port));

        const portResults = await Promise.all(tasks);

        for (const result of portResults) {
            if (result.status === 'open') {
                results.push({
                    ip: result.ip,
                    port: result.port,
                    status: 'online',
                    type: this.getDeviceType(result.port)
                });
            }
        }

        return {
            ip,
            status: results.length > 0 ? 'online' : 'offline',
            openPorts: results
        };
    }
}

// Экспортируем синглтон для удобства
export const networkScanner = new BrowserNetworkScanner();