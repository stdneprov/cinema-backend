from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from passlib.context import CryptContext

# Инициализация роутера
router = APIRouter()

# Модель для сброса пароля
class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/reset-password", response_model=None)
async def reset_password(reset_request: ResetPasswordRequest, request: Request):
    # Получение пула соединений через request.state
    pool = request.state.pool

    query_get_user = "SELECT id, password_hash, need_reset_password FROM users WHERE username = $1"
    query_update_password = """
        UPDATE users
        SET password_hash = $1, need_reset_password = false
        WHERE username = $2
    """

    async with pool.acquire() as conn:
        user = await conn.fetchrow(query_get_user, reset_request.username)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user["need_reset_password"]:
            raise HTTPException(
                status_code=400, detail="Password reset is not required"
            )

        new_password_hash = pwd_context.hash(reset_request.new_password)

        await conn.execute(query_update_password, new_password_hash, reset_request.username)

    return {"message": "Password has been reset successfully"}
