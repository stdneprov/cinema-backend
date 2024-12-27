import falcon
from auth import require_role
import asyncpg

class UsersResource:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    @require_role("admin")
    async def on_get(self, req, resp, id=None):
        async with self.db_pool.acquire() as conn:
            if id:
                user_query = """
                    SELECT id, username, role, expiration_date FROM users WHERE id = $1
                """
                user = await conn.fetchrow(user_query, int(id))
                
                if not user:
                    raise falcon.HTTPNotFound(description="User not found")

                resp.media = {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "expiration_date": user["expiration_date"].isoformat()
                }
            else:
                users_query = """
                    SELECT id, username, role, expiration_date FROM users
                """
                users = await conn.fetch(users_query)
                
                resp.media = [
                    {
                        "id": user["id"],
                        "username": user["username"],
                        "role": user["role"],
                        "expiration_date": user["expiration_date"].isoformat()
                    } for user in users
                ]

    @require_role("admin")
    async def on_post(self, req, resp):
        data = await req.media

        username = data.get("username")
        password = data.get("password")
        role = data.get("role")
        expiration_date = data.get("expiration_date")

        if not all([username, password, role, expiration_date]):
            raise falcon.HTTPBadRequest(description="All fields are required")

        async with self.db_pool.acquire() as conn:
            insert_query = """
                INSERT INTO users (username, password_hash, role, expiration_date)
                VALUES ($1, crypt($2, gen_salt('bf')), $3, $4) RETURNING id
            """
            user_id = await conn.fetchval(insert_query, username, password, role, expiration_date)

        resp.media = {
            "id": user_id,
            "username": username,
            "role": role,
            "expiration_date": expiration_date
        }

    @require_role("admin")
    async def on_put(self, req, resp, id):
        data = await req.media

        username = data.get("username")
        role = data.get("role")

        if not all([username, role]):
            raise falcon.HTTPBadRequest(description="Both username and role are required")

        async with self.db_pool.acquire() as conn:
            update_query = """
                UPDATE users
                SET username = $1, role = $2
                WHERE id = $3 RETURNING id, username, role, expiration_date
            """
            user = await conn.fetchrow(update_query, username, role, int(id))

            if not user:
                raise falcon.HTTPNotFound(description="User not found")

            resp.media = {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "expiration_date": user["expiration_date"].isoformat()
            }

    @require_role("admin")
    async def on_delete(self, req, resp, id):
        async with self.db_pool.acquire() as conn:
            delete_query = """
                DELETE FROM users WHERE id = $1
            """
            result = await conn.execute(delete_query, int(id))

            if result == "DELETE 0":
                raise falcon.HTTPNotFound(description="User not found")

        resp.media = {"message": "User deleted successfully."}