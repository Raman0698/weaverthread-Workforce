```sql
-- PostgreSQL schema for users table

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    date_of_birth DATE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

```python
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional, List
from datetime import datetime, timedelta, date
import bcrypt
import jwt
import uuid
import asyncpg
import os

# Configuration variables (should ideally come from environment variables or config files)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/gym_db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "YOUR_VERY_SECRET_KEY")  # Replace with strong secret in prod
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600

app = FastAPI(title="Gym Backend API")

# Enable CORS for frontend communication
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add frontend domains as per deployment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Pydantic Models

class UserRegisterRequest(BaseModel):
    full_name: constr(strip_whitespace=True, min_length=1, max_length=255)
    email: EmailStr
    password: constr(min_length=8, max_length=128)
    phone: Optional[constr(strip_whitespace=True, max_length=30)] = None
    date_of_birth: Optional[date] = None

    @validator("password")
    def validate_password_strength(cls, v):
        # Simple password strength validation:
        # At least 8 characters, includes at least one uppercase, one lowercase, one number
        import re
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$", v):
            raise ValueError(
                "Password must include at least one uppercase letter, one lowercase letter, and one number."
            )
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    full_name: Optional[constr(strip_whitespace=True, min_length=1, max_length=255)] = None
    email: Optional[EmailStr] = None
    phone: Optional[constr(strip_whitespace=True, max_length=30)] = None
    date_of_birth: Optional[date] = None

    @validator("email")
    def email_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Email cannot be empty string")
        return v

    @validator("full_name")
    def full_name_not_empty(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Full name cannot be empty string")
        return v

    def is_any_field_set(self):
        return any(
            getattr(self, field) is not None
            for field in ("full_name", "email", "phone", "date_of_birth")
        )


class AdminUsersListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


# Database connection pool
@app.on_event("startup")
async def startup():
    app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)


@app.on_event("shutdown")
async def shutdown():
    await app.state.db_pool.close()


# Utility functions


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_user_by_email(conn: asyncpg.Connection, email: str):
    row = await conn.fetchrow(
        "SELECT id, full_name, email, password_hash, phone, date_of_birth, is_admin, created_at "
        "FROM users WHERE email=$1",
        email,
    )
    return row


async def get_user_by_id(conn: asyncpg.Connection, user_id: uuid.UUID):
    row = await conn.fetchrow(
        "SELECT id, full_name, email, password_hash, phone, date_of_birth, is_admin, created_at "
        "FROM users WHERE id=$1",
        user_id,
    )
    return row


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except Exception:
        raise credentials_exception

    async with app.state.db_pool.acquire() as conn:
        user = await get_user_by_id(conn, user_uuid)
        if user is None:
            raise credentials_exception
        # build user dict for return
        user_dict = dict(user)
        return user_dict


async def require_admin_user(current_user=Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin privileges required"
        )
    return current_user


def user_row_to_response(row: asyncpg.Record) -> UserResponse:
    return UserResponse(
        id=row["id"],
        full_name=row["full_name"],
        email=row["email"],
        phone=row["phone"],
        date_of_birth=row["date_of_birth"],
        created_at=row["created_at"],
    )


@app.post("/api/v1/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegisterRequest):
    async with app.state.db_pool.acquire() as conn:
        # Check if email already exists
        existing = await get_user_by_email(conn, user.email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        hashed_password = hash_password(user.password)

        user_id = uuid.uuid4()
        created_at = datetime.utcnow()

        await conn.execute(
            """
            INSERT INTO users (id, full_name, email, password_hash, phone, date_of_birth, created_at, is_admin)
            VALUES ($1, $2, $3, $4, $5, $6, $7, FALSE)
            """,
            user_id,
            user.full_name,
            user.email,
            hashed_password,
            user.phone,
            user.date_of_birth,
            created_at,
        )

        return UserResponse(
            id=user_id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            date_of_birth=user.date_of_birth,
            created_at=created_at,
        )


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(form_data: LoginRequest):
    email = form_data.email
    password = form_data.password

    async with app.state.db_pool.acquire() as conn:
        user = await get_user_by_email(conn, email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        to_encode = {
            "sub": str(user["id"]),
            "is_admin": user["is_admin"],
        }
        access_token = create_access_token(to_encode, timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS))

        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
        )


@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user_profile(current_user=Depends(get_current_user)):
    return user_row_to_response(current_user)


@app.get("/api/v1/admin/users", response_model=AdminUsersListResponse)
async def admin_list_users(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(require_admin_user),
):
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be 1-100")

    offset = (page - 1) * page_size

    async with app.state.db_pool.acquire() as conn:
        users_rows = await conn.fetch(
            """
            SELECT id, full_name, email, phone, date_of_birth, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            page_size,
            offset,
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM users")

        users = [
            UserResponse(
                id=row["id"],
                full_name=row["full_name"],
                email=row["email"],
                phone=row["phone"],
                date_of_birth=row["date_of_birth"],
                created_at=row["created_at"],
            )
            for row in users_rows
        ]
    return AdminUsersListResponse(users=users, total=total, page=page, page_size=page_size)


@app.get("/api/v1/admin/users/{user_id}", response_model=UserResponse)
async def admin_get_user_details(
    user_id: uuid.UUID,
    current_user=Depends(require_admin_user),
):
    async with app.state.db_pool.acquire() as conn:
        user = await get_user_by_id(conn, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user_row_to_response(user)


@app.put("/api/v1/admin/users/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: uuid.UUID,
    user_update: UserUpdateRequest,
    current_user=Depends(require_admin_user),
):
    if not user_update.is_any_field_set():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one field is required")

    async with app.state.db_pool.acquire() as conn:
        user = await get_user_by_id(conn, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # If email is to be changed, check uniqueness
        if user_update.email is not None and user_update.email != user["email"]:
            exists = await get_user_by_email(conn, user_update.email)
            if exists and exists["id"] != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

        # Prepare update query and params dynamically
        set_clauses = []
        params = []
        idx = 1

        def add_set_clause(field_name, value):
            nonlocal idx
            set_clauses.append(f"{field_name} = ${idx}")
            params.append(value)
            idx += 1

        if user_update.full_name is not None:
            add_set_clause("full_name", user_update.full_name)
        if user_update.email is not None:
            add_set_clause("email", user_update.email)
        if user_update.phone is not None:
            add_set_clause("phone", user_update.phone)
        if user_update.date_of_birth is not None:
            add_set_clause("date_of_birth", user_update.date_of_birth)

        if not set_clauses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

        params.append(user_id)
        query = f"""
            UPDATE users SET {', '.join(set_clauses)} WHERE id = ${idx}
        """
        await conn.execute(query, *params)
        updated_user = await get_user_by_id(conn, user_id)

        return user_row_to_response(updated_user)


@app.delete("/api/v1/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: uuid.UUID,
    current_user=Depends(require_admin_user),
):
    async with app.state.db_pool.acquire() as conn:
        user = await get_user_by_id(conn, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        await conn.execute(
            "DELETE FROM users WHERE id = $1",
            user_id,
        )
    return None  # 204 No Content has empty response body
```