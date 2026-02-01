FROM node:18-alpine as build

# ARG для передачи переменных окружения при сборке
ARG VITE_API_URL
ARG VITE_APP_NAME

WORKDIR /app

# Копируем package.json и устанавливаем зависимости
COPY package*.json ./
RUN npm install

# Копируем исходный код
COPY . .

# Устанавливаем переменные окружения для сборки
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_NAME=$VITE_APP_NAME

# Собираем приложение
RUN npm run build

FROM node:18-alpine

WORKDIR /app

# Копируем собранное приложение
COPY --from=build /app/dist ./dist

RUN npm install -g serve

EXPOSE 80

# Запускаем сервер для статики
CMD ["serve", "-s", "dist", "-l", "80"]