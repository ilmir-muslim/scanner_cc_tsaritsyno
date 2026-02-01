FROM nginx:alpine

# Устанавливаем таймзоны
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone

# Копируем конфигурацию
COPY nginx.conf /etc/nginx/nginx.conf

# Создаем папку для логов
RUN mkdir -p /var/log/nginx && \
    touch /var/log/nginx/access.log && \
    touch /var/log/nginx/error.log

# Открываем порты
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]