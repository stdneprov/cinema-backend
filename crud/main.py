import falcon.asgi
import asyncpg
from settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from auth import verify_jwt_token
from movies import MovieResource
from users import UsersResource
from streaming import StreamingResource
from rating import RatingResource
import asyncio

# Middleware
class Middleware:
    async def process_request_async(self, req, resp):
        token = req.get_header('Authorization')
        if token:
            try:
                token = token.split(' ')[1]  # Bearer <token>
                payload = await verify_jwt_token(token)
                req.context['username'] = payload.get('username')
                req.context['role'] = payload.get('role')
            except Exception:
                req.context['username'] = None
                req.context['role'] = None
        else:
            req.context['username'] = None
            req.context['role'] = None

# Функция для создания подключения к базе данных
async def init_db():
    db_pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return db_pool

# Инициализация приложения
async def create_app():
    # Инициализируем подключение к базе данных
    db_pool = await init_db()

    # Создаем ресурсы
    movie_resource = MovieResource(db_pool)
    users_resource = UsersResource(db_pool)
    streaming_resource = StreamingResource()
    rating_resource = RatingResource(db_pool)

    # Создаем приложение с middleware
    app = falcon.asgi.App(middleware=[Middleware()])

    # Добавляем маршруты
    app.add_route('/movies/{id:int}', movie_resource)
    app.add_route('/movies/', movie_resource)
    app.add_route('/users/{id:int}', users_resource)
    app.add_route('/users/', users_resource)
    app.add_route('/stream/{uuid}', streaming_resource)
    app.add_route('/rating/{id:int}', rating_resource)
    app.add_route('/rating/', rating_resource)


    return app

app = None

if __name__ == '__main__':
    # Создаем приложение и запускаем его
    app = asyncio.run(create_app())

    # Запускаем приложение с использованием Uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
