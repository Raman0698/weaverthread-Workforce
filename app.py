from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr
from typing import Optional
import bcrypt
import jwt
import asyncpg
import os
from datetime import datetime, timedelta

# Configurations
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_MINUTES = 60

BCRYPT_SALT_ROUNDS = 12  # industry standard 10-12 rounds

ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "null",
]

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5433/dbname")

app = FastAPI()

# CORS Middleware with strict whitelist and narrow methods/headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False  # no credentials support needed
)

# Database connection pool - global
async def get_db_pool():
    if not hasattr(app.state, "db_pool"):
        app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)
    return app.state.db_pool

# Request models with validation
# Note: Password max length 72 chars ensures no bcrypt truncation
class UserRegister(BaseModel):
    username: constr(min_length=3, max_length=50, strip_whitespace=True)
    password: constr(min_length=8, max_length=72)

class UserLogin(BaseModel):
    username: constr(min_length=3, max_length=50, strip_whitespace=True)
    password: constr(min_length=8, max_length=72)

# Utility functions
def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_SALT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_jwt_token(user_id: int, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_DELTA_MINUTES),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

# Routes
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, pool=Depends(get_db_pool)):
    async with pool.acquire() as conn:
        user_exists = await conn.fetchval(
            "SELECT 1 FROM users WHERE username = $1",
            user.username
        )
        if user_exists:
            # Generic message prevents username harvesting
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Registration failed")
        password_hash = hash_password(user.password)

        await conn.execute(
            "INSERT INTO users (username, password_hash) VALUES ($1, $2)",
            user.username, password_hash
        )
    return {"message": "User registered successfully."}

@app.post("/login")
async def login(user: UserLogin, pool=Depends(get_db_pool)):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, password_hash FROM users WHERE username = $1",
            user.username
        )
        if not row:
            # Do not reveal if username or password is wrong
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid username or password")

        password_hash = row["password_hash"]
        if not verify_password(user.password, password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid username or password")

        token = create_jwt_token(row["id"], user.username)
        return {"access_token": token, "token_type": "bearer"}

# Simple authenticated endpoint example
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    pool=Depends(get_db_pool)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid authentication token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")

    # Verify user still exists
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id, username FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="User not found")
    return {"id": user["id"], "username": user["username"]}

@app.get("/profile")
async def profile(current_user=Depends(get_current_user)):
    return {"id": current_user["id"], "username": current_user["username"]}