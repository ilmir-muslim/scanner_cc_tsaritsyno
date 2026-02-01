#!/bin/bash

# Создаем папку ssl если нет
mkdir -p ../ssl

# Генерируем самоподписанный сертификат
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ../ssl/nginx-selfsigned.key \
    -out ../ssl/nginx-selfsigned.crt \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=Company/OU=IT/CN=46.23.98.207"

# Генерируем Diffie-Hellman параметры (опционально, для повышения безопасности)
openssl dhparam -out ../ssl/dhparam.pem 2048

echo "Сертификаты созданы в папке ssl/"
echo "Файлы:"
echo "  - nginx-selfsigned.crt"
echo "  - nginx-selfsigned.key"
echo "  - dhparam.pem"