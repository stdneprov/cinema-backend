import falcon
from auth import require_role

class RatingResource:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    @require_role("user")
    async def on_get(self, req, resp, movie_id):
        username = req.context['username']  # Получаем username из JWT

        async with self.db_pool.acquire() as conn:
            # Получаем ID пользователя по username
            user_query = "SELECT id FROM users WHERE username = $1"
            user_id = await conn.fetchval(user_query, username)

            if not user_id:
                raise falcon.HTTPUnauthorized(description="User not found")

            # Проверяем рейтинг фильма
            query = """
                SELECT rate FROM ratings
                WHERE user_id = $1 AND movie_id = $2
            """
            rating = await conn.fetchval(query, user_id, int(movie_id))

            if rating is None:
                resp.media = {"message": "No rating set for this movie"}
            else:
                resp.media = {"rating": rating}

    @require_role("user")
    async def on_post(self, req, resp, movie_id):
        username = req.context['username']  # Получаем username из JWT
        data = await req.media

        # Проверка переданных данных
        rate = data.get("rate")
        if rate is None or not (0 <= rate <= 5):
            raise falcon.HTTPBadRequest(description="Rate must be between 0 and 5")

        async with self.db_pool.acquire() as conn:
            # Получаем ID пользователя по username
            user_query = "SELECT id FROM users WHERE username = $1"
            user_id = await conn.fetchval(user_query, username)

            if not user_id:
                raise falcon.HTTPUnauthorized(description="User not found")

            # Проверяем, существует ли фильм
            movie_exists = await conn.fetchval(
                "SELECT 1 FROM movies WHERE id = $1", int(movie_id)
            )
            if not movie_exists:
                raise falcon.HTTPNotFound(description="Movie not found")

            # Вставляем или обновляем рейтинг
            query = """
                INSERT INTO ratings (user_id, movie_id, rate)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, movie_id)
                DO UPDATE SET rate = $3
            """
            await conn.execute(query, user_id, int(movie_id), rate)

        resp.media = {"message": "Rating set successfully"}
