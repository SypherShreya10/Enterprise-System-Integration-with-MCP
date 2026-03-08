from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    },
    "manager_user": {
        "username": "manager_user",
        "password": "manager123",
        "role": "manager"
    },
    "sales_user": {
        "username": "sales_user",
        "password": "sales123",
        "role": "sales_agent"
    },
    "operator_user": {
        "username": "operator_user",
        "password": "operator123",
        "role": "operator"
    },
    "viewer_user": {
        "username": "viewer_user",
        "password": "viewer123",
        "role": "viewer"
    }
}

def authenticate_user(username, password):
    user = FAKE_USERS_DB.get(username)

    if not user:
        return False

    if password != user["password"]:
        return False

    return user


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None