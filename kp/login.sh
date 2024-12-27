#!/bin/bash

# Адрес API сервера
BASE_URL="http://127.0.0.1:8000"

# Данные для входа
USERNAME="root"  # Замените на имя пользователя
PASSWORD="password"  # Замените на пароль

# Формирование JSON данных для запроса
LOGIN_PAYLOAD="{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}"

# Выполнение POST-запроса для получения токена
AUTH_TOKEN=$(curl -X 'POST' \
  "$BASE_URL/api/login" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_PAYLOAD" | jq -r '.access_token')

# Проверка успешности получения токена
if [ "$AUTH_TOKEN" == "null" ] || [ -z "$AUTH_TOKEN" ]; then
  echo "Ошибка: не удалось получить токен. Проверьте правильность логина и пароля."
  exit 1
fi

# Вывод полученного токена
echo "Получен токен: $AUTH_TOKEN"
