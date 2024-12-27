from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from asyncpg import Pool
from typing import Optional
from pydantic import BaseModel
from auth import get_current_user  # Импорт функции для получения текущего пользователя

# Инициализация роутера
router = APIRouter()

class RateRequest(BaseModel):
    rate: int


# Получение текущего рейтинга фильма
@router.get("/movies/{movie_id}/rating")
async def get_movie_rating(request: Request, movie_id: int, user: dict = Depends(get_current_user)):
    pool: Pool = request.state.pool
    query = """
        SELECT rate FROM ratings WHERE movie_id = $1 AND user_id = $2
    """
    async with pool.acquire() as conn:
        rating = await conn.fetchrow(query, movie_id, int(user["sub"]))

    if rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")

    return {"rating": rating["rate"]}

# Роут для установки или обновления рейтинга для фильма
@router.post("/movies/{movie_id}/rating")
async def rate_movie(
    request: Request, 
    movie_id: int, 
    rate: RateRequest,
    user: dict = Depends(get_current_user),
):
    pool: Pool = request.state.pool

    # Проверка, чтобы рейтинг был в допустимом диапазоне
    if rate.rate < 0 or rate.rate > 5:
        raise HTTPException(status_code=400, detail="Rate must be between 0 and 5")

    # Проверяем, поставил ли уже пользователь рейтинг для этого фильма
    query = """
        SELECT * 
        FROM ratings 
        WHERE user_id = $1 AND movie_id = $2
    """
    async with pool.acquire() as conn:
        existing_rating = await conn.fetchrow(query, int(user["sub"]), movie_id)
    
    if existing_rating:
        # Если рейтинг существует, обновляем его
        query_update = """
            UPDATE ratings 
            SET rate = $1 
            WHERE user_id = $2 AND movie_id = $3
        """
        async with pool.acquire() as conn:
            await conn.execute(query_update, rate.rate, int(user["sub"]), movie_id)
        return JSONResponse(content={"message": "Rating updated successfully"})
    else:
        # Если рейтинга нет, вставляем новый
        query_insert = """
            INSERT INTO ratings (user_id, movie_id, rate) 
            VALUES ($1, $2, $3)
        """
        async with pool.acquire() as conn:
            await conn.execute(query_insert, int(user["sub"]), movie_id, rate.rate)
        return JSONResponse(content={"message": "Rating added successfully"})
