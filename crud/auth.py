import jwt
import falcon.asgi
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from falcon import HTTPUnauthorized
import os

# Декоратор для проверки роли
def require_role(role):
    def decorator(func):
        async def wrapper(self, req, resp, *args, **kwargs):
            if req.context.get('role') != role:
                raise falcon.HTTPForbidden(description='Access denied')
            return await func(self, req, resp, *args, **kwargs)
        return wrapper
    return decorator

async def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        return payload
    except ExpiredSignatureError:
        raise HTTPUnauthorized(description='Token has expired')
    except InvalidTokenError:
        raise HTTPUnauthorized(description='Invalid token')

async def get_username(payload: dict):
    return payload.get('username')

async def get_user_role(payload: dict):
    return payload.get('role')

