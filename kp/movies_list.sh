#!/bin/bash

# Базовый URL API сервера
BASE_URL="http://127.0.0.1:8000"

# Ваш авторизационный токен (замените на реальный токен)
AUTH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzM1MjM5MDYxfQ.N8gW0rUci-ymzG_5XIhZJuKXSzajimbhnnb809mwjN4"

# Тест 1: Получение всех фильмов без параметров
echo "Test 1: Get all movies"
curl -X 'GET' \
  "${BASE_URL}/api/movies" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $AUTH_TOKEN"

echo -e "\n\n"

# Тест 2: Поиск фильма по названию
SEARCH_QUERY="Test"  # Замените на реальное название
echo "Test 2: Search movies by title (search='$SEARCH_QUERY')"
curl -X 'GET' \
  "${BASE_URL}/api/movies?search=${SEARCH_QUERY}" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $AUTH_TOKEN"

echo -e "\n\n"

# Тест 3: Сортировка по рейтингу (по убыванию)
echo "Test 3: Get movies sorted by rating (descending)"
curl -X 'GET' \
  "${BASE_URL}/api/movies?sort_by_rating=true" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $AUTH_TOKEN"

echo -e "\n\n"

# Тест 4: Поиск и сортировка одновременно
echo "Test 4: Search and sort by rating (descending)"
curl -X 'GET' \
  "${BASE_URL}/api/movies?search=${SEARCH_QUERY}&sort_by_rating=true" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $AUTH_TOKEN"

echo -e "\n\n"

echo "All tests completed!"
