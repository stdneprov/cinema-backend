curl -X POST http://127.0.0.1:8000/api/reset-password \
-H "Content-Type: application/json" \
-d '{
    "username": "root",
    "new_password": "password"
}'
