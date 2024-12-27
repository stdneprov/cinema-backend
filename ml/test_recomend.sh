#!/bin/bash

# URL сервера
URL="http://localhost:8080/recommend"

# Пример данных для запроса
DATA=$(cat <<EOF
{
  "title": "Rent-a-Cat (2012)"
}
EOF
)

# Выполнение запроса с помощью curl
curl -X POST $URL \
     -H "Content-Type: application/json" \
     -d "$DATA" \
     -w "\nHTTP Status: %{http_code}\n" \
     -o response.json

# Проверка ответа
if [ $? -eq 0 ]; then
  echo "Тест выполнен успешно. Ответ сохранен в response.json."
else
  echo "Ошибка при выполнении запроса."
fi

# Печать ответа
echo "Ответ сервера:"
cat response.json
