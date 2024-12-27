from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from passlib.context import CryptContext

# Инициализация роутера
router = APIRouter()

# Модель для регистрации пользователя
class RegisterRequest(BaseModel):
    username: str
    password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", response_model=None)
async def register(register_request: RegisterRequest, request: Request):
    # Получение пула соединений через request.state
    pool = request.state.pool

    query_check_username = "SELECT 1 FROM users WHERE username = $1"
    query_insert_user = """
        INSERT INTO users (username, password_hash, role, need_reset_password, last_login, last_action)
        VALUES ($1, $2, 'user', false, NULL, NULL)
    """

    async with pool.acquire() as conn:
        # Проверяем, существует ли пользователь с таким именем
        user_exists = await conn.fetchval(query_check_username, register_request.username)

        if user_exists:
            raise HTTPException(status_code=400, detail="Username already taken")

        # Хэшируем пароль
        hashed_password = pwd_context.hash(register_request.password)

        # Вставляем нового пользователя
        await conn.execute(query_insert_user, register_request.username, hashed_password)

    return {"message": "User registered successfully"}
