#!/bin/bash

# Базовый URL API сервера
BASE_URL="http://127.0.0.1:8000"

# Токен авторизации (замените на ваш действующий токен)
AUTH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzM1MjM5MDYxfQ.N8gW0rUci-ymzG_5XIhZJuKXSzajimbhnnb809mwjN4"

# ID фильма для тестирования
MOVIE_ID=1  # Замените на реальный ID фильма, который хотите тестировать

# Тест 1: Получение текущего рейтинга пользователя для фильма
echo "Test 1: Get current rating for movie ID $MOVIE_ID"
curl -X 'GET' \
  "${BASE_URL}/api/movies/${MOVIE_ID}/rating" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H 'accept: application/json'

echo -e "\n\n"

# Тест 2: Установка или обновление рейтинга для фильма
MOVIE_ID=1 

NEW_RATING=4  # Замените на рейтинг, который вы хотите поставить (от 0 до 5)

echo "Test 2: Set or update rating for movie ID $MOVIE_ID with rating $NEW_RATING"
curl -X 'POST' \
  "${BASE_URL}/api/movies/${MOVIE_ID}/rating" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"rate":'"$NEW_RATING"'}'

echo -e "\n\n"
