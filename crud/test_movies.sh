#!/bin/bash

# Установим базовые URL
BASE_URL="http://localhost:8000"
MOVIE_API="$BASE_URL/movies"

# Токен авторизации (поменяйте на реальный токен)
AUTH_TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJyb290Iiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNjcyNTMxMjAwLCJleHAiOjE3OTY4NjA4MDB9.Bdij1sv3THfziMMzgFdTRCHY03rzZy2UIfn8lzlsd7E"

# Заголовки для авторизации
AUTH_HEADER="Authorization: $AUTH_TOKEN"

# Создание фильма (POST)
echo "Creating a new movie..."
response=$(curl -s -w "%{http_code}" -o response.json -X POST "$MOVIE_API/" \
    -H "Content-Type: multipart/form-data" \
    -H "$AUTH_HEADER" \
    -F "title=Test Movie" \
    -F "description=Test description" \
    -F "actors=Actor 1, Actor 2" \
    -F "genre=Action" \
    -F "year_of_creation=2024" \
    -F "file=@movie.mp4")

status_code=$(tail -n 1 <<< "$response")
if [ "$status_code" -eq 200 ]; then
    echo "Movie created successfully."
    movie_id=$(jq -r '.id' response.json)
    echo "Movie ID: $movie_id"
else
    echo "Failed to create movie. Status code: $status_code"
    cat response.json
    exit 1
fi

# Получение списка фильмов (GET)
echo "Fetching movies list..."
curl -s -X GET "$MOVIE_API/" -H "$AUTH_HEADER" -o response.json
cat response.json

# Получение конкретного фильма по ID (GET)
echo "Fetching movie with ID $movie_id..."
curl -s -X GET "$MOVIE_API/$movie_id" -H "$AUTH_HEADER" -o response.json
cat response.json

# Удаление фильма (DELETE)
echo "Deleting movie with ID $movie_id..."
delete_response=$(curl -s -w "%{http_code}" -o response.json -X DELETE "$MOVIE_API/$movie_id" -H "$AUTH_HEADER")

delete_status_code=$(tail -n 1 <<< "$delete_response")
if [ "$delete_status_code" -eq 200 ]; then
    echo "Movie deleted successfully."
else
    echo "Failed to delete movie. Status code: $delete_status_code"
    cat response.json
    exit 1
fi
