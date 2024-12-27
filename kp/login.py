from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext
from settings import SECRET_KEY, ALGORITHM, pwd_context
from datetime import datetime, timedelta

# Инициализация роутера
router = APIRouter()

# Модель для входных данных
class LoginRequest(BaseModel):
    username: str
    password: str

# Модель для возвращаемого токена
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Функция для проверки пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Функция для создания JWT токена
def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta  # Устанавливаем время истечения
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest, request: Request):
    # Получаем пул соединений из request.state
    pool = request.state.pool

    query = "SELECT id, password_hash, role, need_reset_password FROM users WHERE username = $1"
    async with pool.acquire() as conn:
        user = await conn.fetchrow(query, login_request.username)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if user["need_reset_password"]:
            raise HTTPException(status_code=403, detail="Password reset required")

        if not verify_password(login_request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Создаем JWT токен с ID пользователя и ролью
        token_data = {
            "sub": str(user["id"]),  # ID пользователя
            "role": user["role"]     # Роль пользователя
        }
        access_token = create_access_token(data=token_data)

        # Возвращаем токен
        return TokenResponse(access_token=access_token, token_type="bearer")
