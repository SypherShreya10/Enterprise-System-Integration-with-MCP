# MCP server with login + protected endpoint (main.py)
# main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta

from auth import authenticate_user, create_access_token, decode_token

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=30),
    )
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload["sub"]

@app.get("/protected")
def protected_endpoint(current_user: str = Depends(get_current_user)):
    return {
        "message": f"Hello {current_user}, you are authenticated!",
        "status": "ACCESS_GRANTED"
    }
