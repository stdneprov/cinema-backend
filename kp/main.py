from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Импортируем CORSMiddleware
from asyncpg import create_pool
from settings import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT
from login import router as login_router
from resetPassword import router as reset_password_router
from register import router as register_router
from front import router as front_router
from movies import router as movies_router
from rating import router as rating_router

app = FastAPI()

# Пул соединений
pool = None

# Разрешенные источники для CORS (можно настроить для конкретных доменов или использовать '*' для всех)
origins = [
    "*"
]

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Можно указать '*' для всех источников, но лучше ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)

@app.on_event("startup")
async def startup():
    global pool
    pool = await create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
    )
    print("Database connection pool established")


@app.on_event("shutdown")
async def shutdown():
    global pool
    if pool:
        await pool.close()
        print("Database connection pool closed")


@app.middleware("http")
async def db_connection_middleware(request, call_next):
    request.state.pool = pool  # Передаем пул соединений через request.state
    response = await call_next(request)
    return response

# Подключение маршрутов
app.include_router(login_router, prefix="/api")
app.include_router(reset_password_router, prefix="/api")
app.include_router(register_router, prefix="/api")
app.include_router(movies_router, prefix="/api")
app.include_router(rating_router, prefix="/api")
app.include_router(front_router, prefix="")
