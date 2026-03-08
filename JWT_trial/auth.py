# auth.py
from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "CHANGE_THIS_SECRET_IN_REAL_PROJECT"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Simple fake user database (no hashing for Level 1)
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "password": "admin123",
    }   
}

def authenticate_user(username: str, password: str):
    user = FAKE_USERS_DB.get(username)
    if not user:
        return False
    if password != user["password"]:
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
