from fastapi import APIRouter, HTTPException, Request, File, UploadFile, Header, Form, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from asyncpg import Pool
from typing import List, Optional
import os
import aiofiles
from auth import get_current_user, require_admin_or_super_admin
from uuid import uuid4

# Инициализация роутера
router = APIRouter()

# Папка для хранения загруженных файлов
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Модель для отображения фильма
class MovieResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    actors: Optional[str]
    genre: Optional[str]
    year_of_creation: int
    file_id: str
    rating: Optional[float]
    your_rating: Optional[int]


# Получение списка фильмов
@router.get("/movies", response_model=List[MovieResponse])
async def get_movies(
    request: Request,
    search: Optional[str] = None,
    sort_by_rating: Optional[bool] = True,
    user: dict = Depends(get_current_user)
):
    pool: Pool = request.state.pool

    query = f"""SELECT m.*, r.rate AS your_rating 
        FROM 
            full_movies_info m
        LEFT JOIN 
            ratings r ON r.movie_id = m.id AND r.user_id = $1"""
    query_params = [int(user['sub'])]

    if search:
        query += " WHERE title ILIKE $2"
        query_params.append(f"%{search}%")

    if sort_by_rating:
        query += """
            ORDER BY 
                CASE 
                    WHEN rating IS NULL THEN 1 
                    ELSE 0 
                END, 
                rating DESC"""
        
    query += " LIMIT 100"

    async with pool.acquire() as conn:
        movies = await conn.fetch(query, *query_params)

    return [
        MovieResponse(
            id=movie["id"],
            title=movie["title"],
            description=movie.get("description"),
            actors=movie.get("actors"),
            genre=movie.get("genre"),
            year_of_creation=movie["year_of_creation"],
            file_id=movie["file_id"],
            rating=movie["rating"],
            your_rating=movie['your_rating']
        )
        for movie in movies
    ]


# Создание нового фильма с загрузкой файла
@router.post("/movies", response_model=MovieResponse)
async def create_movie(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    actors: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    year_of_creation: int = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(require_admin_or_super_admin)
):
    pool: Pool = request.state.pool

    # Проверка формата файла
    if not file.filename.endswith((".mp4", ".avi", ".mov")):
        raise HTTPException(status_code=400, detail="Invalid file format. Supported formats: .mp4, .avi, .mov")

    query_check_title = "SELECT * FROM movies WHERE title = $1"
    async with pool.acquire() as conn:
        existing_movie = await conn.fetchrow(query_check_title, title)

    if existing_movie:
        raise HTTPException(status_code=400, detail="Movie with this title already exists")

    # Генерация уникального имени файла
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

    # Асинхронная запись файла
    async with aiofiles.open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            await buffer.write(chunk)

    query_create_movie = """
        INSERT INTO movies (title, description, actors, genre, year_of_creation, file_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    """
    async with pool.acquire() as conn:
        new_movie = await conn.fetchrow(
            query_create_movie,
            title,
            description,
            actors,
            genre,
            year_of_creation,
            unique_filename
        )

    query_get_movie = "SELECT * FROM full_movies_info WHERE id = $1"
    async with pool.acquire() as conn:
        created_movie = await conn.fetchrow(query_get_movie, new_movie["id"])

    return MovieResponse(
        id=created_movie["id"],
        title=created_movie["title"],
        description=created_movie.get("description"),
        actors=created_movie.get("actors"),
        genre=created_movie.get("genre"),
        year_of_creation=created_movie["year_of_creation"],
        file_id=created_movie["file_id"],
        rating=created_movie["rating"]
    )


# Стриминг видео с поддержкой перемотки
@router.get("/movies/stream/{uuid}")
async def stream_movie(uuid: str, range: Optional[str] = Header(None)):
    file_path = os.path.join(UPLOAD_FOLDER, uuid)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    file_size = os.path.getsize(file_path)

    # Если заголовок Range не указан
    if not range:
        async def full_streamer():
            async with aiofiles.open(file_path, "rb") as file:
                while chunk := await file.read(1024 * 1024):
                    yield chunk
        return StreamingResponse(full_streamer(), media_type="video/mp4", headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size)
        })

    # Парсим Range
    try:
        start, end = range.replace("bytes=", "").split("-")
        start = int(start)
        end = int(end) if end else file_size - 1
    except ValueError:
        raise HTTPException(status_code=416, detail="Invalid Range header")

    async def partial_streamer():
        length = end - start + 1
        async with aiofiles.open(file_path, "rb") as file:
            await file.seek(start)
            while length > 0:
                chunk_size = min(1024 * 1024, length)
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                length -= len(chunk)

    return StreamingResponse(partial_streamer(), status_code=206, media_type="video/mp4", headers={
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
    })

# Стриминг видео с поддержкой перемотки
@router.get("/movies/streamById/{id}")
async def stream_by_id_movie(request: Request, id: int, range: Optional[str] = Header(None)):
    pool: Pool = request.state.pool

    query = f"""SELECT file_id
        FROM 
            full_movies_info 
        WHERE id = $1"""

    async with pool.acquire() as conn:
        uuid = await conn.fetch(query, id)
    print(uuid)
    file_path = os.path.join(UPLOAD_FOLDER, uuid[0]['file_id'])

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    file_size = os.path.getsize(file_path)

    # Если заголовок Range не указан
    if not range:
        async def full_streamer():
            async with aiofiles.open(file_path, "rb") as file:
                while chunk := await file.read(1024 * 1024):
                    yield chunk
        return StreamingResponse(full_streamer(), media_type="video/mp4", headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size)
        })

    # Парсим Range
    try:
        start, end = range.replace("bytes=", "").split("-")
        start = int(start)
        end = int(end) if end else file_size - 1
    except ValueError:
        raise HTTPException(status_code=416, detail="Invalid Range header")

    async def partial_streamer():
        length = end - start + 1
        async with aiofiles.open(file_path, "rb") as file:
            await file.seek(start)
            while length > 0:
                chunk_size = min(1024 * 1024, length)
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                length -= len(chunk)

    return StreamingResponse(partial_streamer(), status_code=206, media_type="video/mp4", headers={
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
    })

