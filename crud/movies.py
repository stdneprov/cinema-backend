import falcon
import aiofiles
import uuid
from falcon import media
from settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY
from auth import require_role
from minio import Minio


class MovieResource:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )

    async def on_get(self, req, resp, id=None):
        if id:
            # Fetch movie by ID
            async with self.db_pool.acquire() as conn:
                movie_query = """
                    SELECT * FROM full_movies_info WHERE id = $1
                """
                movie = await conn.fetchrow(movie_query, int(id))

                if not movie:
                    raise falcon.HTTPNotFound(description="Movie not found")

                resp.media = {
                    "id": movie["id"],
                    "title": movie["title"],
                    "description": movie["description"],
                    "actors": movie["actors"],
                    "genre": movie["genre"],
                    "year_of_creation": movie["year_of_creation"],
                    "file_id": movie["file_id"],
                    "rating": movie["rating"]
                }
        else:
            # Fetch movies by title and sort by rating
            title = req.get_param("title")  # optional query param for movie title
            sort = req.get_param("sort", default="desc")  # optional query param for sort order (default: 'desc')

            if sort not in ["asc", "desc"]:
                raise falcon.HTTPBadRequest(description="Invalid sort order. Use 'asc' or 'desc'.")

            # Build query
            query = """
                SELECT * FROM full_movies_info WHERE title ILIKE $1
                ORDER BY rating {sort} LIMIT 50
            """.format(sort=sort)

            # Perform the search query with title parameter (case-insensitive)
            async with self.db_pool.acquire() as conn:
                movies = await conn.fetch(query, f"%{title}%")

            # If no movies found
            if not movies:
                raise falcon.HTTPNotFound(description="No movies found with that title")

            # Format the result
            resp.media = [
                {
                    "id": movie["id"],
                    "title": movie["title"],
                    "description": movie["description"],
                    "actors": movie["actors"],
                    "genre": movie["genre"],
                    "year_of_creation": movie["year_of_creation"],
                    "file_id": movie["file_id"],
                    "rating": movie["rating"]
                } for movie in movies
            ]

    @require_role("admin")
    async def on_post(self, req, resp):
        try:
            form = await req.get_media(media.MultipartFormHandler)
        except Exception:
            raise falcon.HTTPBadRequest(description="Invalid form data")

        # Extract fields
        title = form.get("title")
        description = form.get("description")
        actors = form.get("actors")
        genre = form.get("genre")
        year_of_creation = form.get("year_of_creation")
        file = form.get("file")

        if not all([title, description, actors, genre, year_of_creation, file]):
            raise falcon.HTTPBadRequest(description="All fields are required")

        # Ensure year is an integer
        try:
            year_of_creation = int(year_of_creation)
        except ValueError:
            raise falcon.HTTPBadRequest(description="Year of creation must be an integer")

        # Generate file ID and file name
        file_id = str(uuid.uuid4())
        file_name = f"movies/{file_id}"

        # Upload the file to MinIO
        try:
            self.minio_client.put_object(
                bucket_name="movies",
                object_name=file_name,
                data=file.file,
                length=-1,  # Let MinIO handle file size
                content_type=file.type
            )
        except Exception as e:
            raise falcon.HTTPInternalServerError(description=f"Failed to upload file: {str(e)}")

        # Insert into database
        async with self.db_pool.acquire() as conn:
            insert_query = """
                INSERT INTO movies (title, description, actors, genre, year_of_creation, file_id)
                VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
            """
            movie_id = await conn.fetchval(
                insert_query, title, description, actors, genre, year_of_creation, file_id
            )

        resp.media = {
            "id": movie_id,
            "title": title,
            "description": description,
            "actors": actors,
            "genre": genre,
            "year_of_creation": year_of_creation
        }

    @require_role("admin")
    async def on_delete(self, req, resp, id):
        async with self.db_pool.acquire() as conn:
            delete_query = """
                DELETE FROM movies WHERE id = $1
            """
            result = await conn.execute(delete_query, int(id))

            if result == "DELETE 0":
                raise falcon.HTTPNotFound(description="Movie not found")

        resp.media = {"message": "Movie deleted successfully."}

