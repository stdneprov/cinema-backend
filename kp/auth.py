from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from settings import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin_or_super_admin(user: dict = Depends(get_current_user)):
    if user["role"] not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Access forbidden")
