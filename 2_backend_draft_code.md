```sql
-- PostgreSQL schema for Gym Registration System

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(254) UNIQUE NOT NULL,
    username VARCHAR(20) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index on username and email for faster lookup (unique constraint enforces uniqueness)
CREATE UNIQUE INDEX idx_users_email ON users (email);
CREATE UNIQUE INDEX idx_users_username ON users (username);
```

```python
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr, validator
import re
import bcrypt
import uuid
from asyncpg import create_pool, Pool
import os

app = FastAPI()

# CORS Configuration - allow only these origins
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# Database connection pool (global)
db_pool: Pool = None

# Password validation regex patterns
lowercase_re = re.compile(r'[a-z]')
uppercase_re = re.compile(r'[A-Z]')
digit_re = re.compile(r'\d')
special_char_re = re.compile(r'[^A-Za-z0-9]')

USERNAME_REGEX = r'^[A-Za-z0-9_]{3,20}$'

class RegisterRequest(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=20)
    password: constr(min_length=8, max_length=72)  # bcrypt max 72 bytes

    @validator('username')
    def username_valid(cls, v):
        if not re.match(USERNAME_REGEX, v):
            raise ValueError('Username must be 3-20 characters long, alphanumeric or underscores only')
        return v

    @validator('password')
    def password_strong(cls, v):
        if not lowercase_re.search(v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not uppercase_re.search(v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not digit_re.search(v):
            raise ValueError('Password must contain at least one digit')
        if not special_char_re.search(v):
            raise ValueError('Password must contain at least one special character')
        return v

class RegisterResponseSuccess(BaseModel):
    message: str
    userId: str

class RegisterResponseError(BaseModel):
    error: str

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await create_pool(
        dsn=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gymdb"),
        min_size=1,
        max_size=10
    )

@app.on_event("shutdown")
async def shutdown():
    await db_pool.close()


@app.post("/api/register", status_code=status.HTTP_201_CREATED, responses={
    201: {"model": RegisterResponseSuccess},
    400: {"model": RegisterResponseError},
})
async def register_user(register: RegisterRequest):
    email = register.email
    username = register.username
    password = register.password

    # Hash password with bcrypt
    # bcrypt requires bytes input, password max length 72 bytes enforced by Pydantic
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    async with db_pool.acquire() as connection:
        # Check if email or username already exists
        existing = await connection.fetchrow(
            """SELECT id FROM users WHERE email=$1 OR username=$2""",
            email, username
        )
        if existing:
            # More specific error messaging if possible
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )

        # Insert new user
        user_id = str(uuid.uuid4())
        try:
            await connection.execute(
                """
                INSERT INTO users (id, email, username, password_hash)
                VALUES ($1, $2, $3, $4)
                """,
                user_id, email, username, hashed
            )
        except Exception as e:
            # Generic error catch for uniqueness violation or other db errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database error during registration"
            ) from e

    return RegisterResponseSuccess(
        message="User registered successfully",
        userId=user_id
    )
```