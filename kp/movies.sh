#!/bin/bash

# Адрес API сервера
BASE_URL="http://127.0.0.1:8000"

# Укажите путь к файлу
MOVIE_FILE_PATH="/Users/stdneprov/code/PythonProject/kp/movie.mp4"  # Измените на корректный путь

# Авторизационный токен (если у вас уже есть токен)
AUTH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzM1MjM5MDYxfQ.N8gW0rUci-ymzG_5XIhZJuKXSzajimbhnnb809mwjN4"  # Замените на ваш JWT токен

# Проверка существования файла
if [ ! -f "$MOVIE_FILE_PATH" ]; then
  echo "Ошибка: Файл не найден по пути $MOVIE_FILE_PATH"
  exit 1
fi

echo "Файл найден: $MOVIE_FILE_PATH"

# Тест 2: Создание фильма с загрузкой файла
echo "Test 2: Create a new movie with file upload"

# Используем 'curl' с правильными параметрами
curl -X POST \
  "$BASE_URL/api/movies" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "title=Best Movie" \
  -F "description=Test Desc" \
  -F "actors=Actor 1" \
  -F "genre=Drama" \
  -F "year_of_creation=2023" \
  -F "file=@$MOVIE_FILE_PATH"

echo -e "\n\n"
