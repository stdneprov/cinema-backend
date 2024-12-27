import asyncio
import asyncpg
import os
from dotenv import load_dotenv


# Загружаем переменные окружения из .env файла
load_dotenv()

async def fetch_users_from_pool(pool):
    """Функция для выборки пользователей из таблицы users, используя пул соединений."""
    try:
        # Получаем соединение из пула
        async with pool.acquire() as conn:
            # Выполняем запрос
            query = "SELECT * FROM users;"
            users = await conn.fetch(query)

            # Обработка и вывод результатов
            for user in users:
                print(f"ID: {user['id']}, Username: {user['username']}, Role: {user['role']}")

    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")


async def main():
    """Основная функция для создания пула соединений и вызова функции выборки данных."""
    try:
        # Получаем параметры подключения из переменных окружения
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", 5432)  # Если не указано, используем порт по умолчанию 5432

        # Создаем пул соединений
        pool = await asyncpg.create_pool(
            user=user,
            password=password,
            database=database,
            host=host,
            port=port
        )
        print("Пул соединений создан!")

        # Выполняем запрос к базе данных
        await fetch_users_from_pool(pool)

    except Exception as e:
        print(f"Ошибка при подключении или создании пула: {e}")

    finally:
        # Закрываем пул соединений (всегда вызывается)
        if 'pool' in locals() and pool:
            await pool.close()
            print("Пул соединений закрыт.")

# Запуск основного процесса
if __name__ == "__main__":
    asyncio.run(main())
