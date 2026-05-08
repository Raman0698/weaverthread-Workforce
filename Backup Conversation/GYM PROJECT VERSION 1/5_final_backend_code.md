```python
# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, constr, ValidationError
from typing import Optional, List
import asyncpg
import os
import uvicorn
from datetime import datetime, timedelta

# --- CONFIGURATION ---

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/mydb")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secure-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Allowed CORS origins, explicit list or ["*"] for dev (adjust for production)
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "https://your-frontend-domain.com",
]

# --- SECURITY SETUP ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

# --- Pydantic Models ---

# User models
class UserCreate(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=8)

class UserPublic(BaseModel):
    id: int
    email: EmailStr
    username: str

class UserInDB(UserPublic):
    hashed_password: str


# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# Post models
class PostCreate(BaseModel):
    title: constr(min_length=1, max_length=200)
    content: constr(min_length=1)

class PostPublic(BaseModel):
    id: int
    author_id: int
    title: str
    content: str
    created_at: datetime

# Comment models
class CommentCreate(BaseModel):
    content: constr(min_length=1)

class CommentPublic(BaseModel):
    id: int
    post_id: int
    author_id: int
    content: str
    created_at: datetime


# --- UTILS ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


# --- DATABASE ---

class Database:
    def __init__(self, dsn):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=self.dsn)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)


db = Database(DATABASE_URL)

# --- APP INSTANCE ---

app = FastAPI(title="Secure FastAPI backend with JWT auth and asyncpg")


# --- MIDDLEWARE ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DEPENDENCIES ---

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception

    user_row = await db.fetchrow(
        "SELECT id, email, username, hashed_password FROM users WHERE username = $1",
        token_data.username,
    )
    if not user_row:
        raise credentials_exception

    user = UserInDB(
        id=user_row["id"],
        email=user_row["email"],
        username=user_row["username"],
        hashed_password=user_row["hashed_password"],
    )
    return user


# --- ROUTES ---

# Health check
@app.get("/api/v1/health", status_code=200)
async def health():
    return {"status": "ok"}


# User registration
@app.post("/api/v1/users", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
async def create_user(user: UserCreate):
    # Check if username or email already exists
    existing = await db.fetchrow(
        "SELECT id FROM users WHERE username = $1 OR email = $2",
        user.username, user.email
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")

    hashed_password = get_password_hash(user.password)
    record = await db.fetchrow(
        """
        INSERT INTO users (email, username, hashed_password)
        VALUES ($1, $2, $3)
        RETURNING id, email, username
        """,
        user.email, user.username, hashed_password
    )
    return UserPublic(**record)


# Token generation (login)
@app.post("/api/v1/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_row = await db.fetchrow(
        "SELECT id, email, username, hashed_password FROM users WHERE username = $1",
        form_data.username
    )
    if not user_row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")

    if not verify_password(form_data.password, user_row["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user_row["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


# Get current user's profile
@app.get("/api/v1/users/me", response_model=UserPublic)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user


# Get user by ID (only allow self or extended roles could be implemented)
@app.get("/api/v1/users/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, current_user: UserInDB = Depends(get_current_user)):
    user_row = await db.fetchrow(
        "SELECT id, email, username FROM users WHERE id = $1",
        user_id
    )
    if not user_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # For this example, only self-access allowed:
    if user_row["id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this user")
    return UserPublic(**user_row)


# Create a post
@app.post("/api/v1/posts", status_code=status.HTTP_201_CREATED, response_model=PostPublic)
async def create_post(post: PostCreate, current_user: UserInDB = Depends(get_current_user)):
    record = await db.fetchrow(
        """
        INSERT INTO posts (author_id, title, content, created_at)
        VALUES ($1, $2, $3, NOW())
        RETURNING id, author_id, title, content, created_at
        """,
        current_user.id, post.title, post.content
    )
    return PostPublic(**record)


# List all posts (public)
@app.get("/api/v1/posts", response_model=List[PostPublic])
async def list_posts(skip: int = 0, limit: int = 50):
    rows = await db.fetch(
        """
        SELECT id, author_id, title, content, created_at
        FROM posts
        ORDER BY created_at DESC
        OFFSET $1 LIMIT $2
        """,
        skip, limit
    )
    return [PostPublic(**row) for row in rows]


# Get a post by id
@app.get("/api/v1/posts/{post_id}", response_model=PostPublic)
async def get_post(post_id: int):
    row = await db.fetchrow(
        """
        SELECT id, author_id, title, content, created_at
        FROM posts
        WHERE id = $1
        """,
        post_id
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return PostPublic(**row)


# Update a post (only author)
@app.put("/api/v1/posts/{post_id}", response_model=PostPublic)
async def update_post(post_id: int, post: PostCreate, current_user: UserInDB = Depends(get_current_user)):
    # Check ownership
    existing_post = await db.fetchrow("SELECT author_id FROM posts WHERE id = $1", post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if existing_post["author_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

    updated = await db.fetchrow(
        """
        UPDATE posts
        SET title = $1, content = $2
        WHERE id = $3
        RETURNING id, author_id, title, content, created_at
        """,
        post.title, post.content, post_id
    )
    return PostPublic(**updated)


# Delete a post (only author)
@app.delete("/api/v1/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, current_user: UserInDB = Depends(get_current_user)):
    existing_post = await db.fetchrow("SELECT author_id FROM posts WHERE id = $1", post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if existing_post["author_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

    await db.execute("DELETE FROM posts WHERE id = $1", post_id)
    return


# Create a comment on a post
@app.post("/api/v1/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED, response_model=CommentPublic)
async def create_comment(post_id: int, comment: CommentCreate, current_user: UserInDB = Depends(get_current_user)):
    # Verify post exists
    post_exists = await db.fetchrow("SELECT id FROM posts WHERE id = $1", post_id)
    if not post_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    record = await db.fetchrow(
        """
        INSERT INTO comments (post_id, author_id, content, created_at)
        VALUES ($1, $2, $3, NOW())
        RETURNING id, post_id, author_id, content, created_at
        """,
        post_id, current_user.id, comment.content
    )
    return CommentPublic(**record)


# List comments for a post
@app.get("/api/v1/posts/{post_id}/comments", response_model=List[CommentPublic])
async def list_comments(post_id: int):
    # Verify post exists
    post_exists = await db.fetchrow("SELECT id FROM posts WHERE id = $1", post_id)
    if not post_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    rows = await db.fetch(
        """
        SELECT id, post_id, author_id, content, created_at
        FROM comments
        WHERE post_id = $1
        ORDER BY created_at ASC
        """,
        post_id
    )
    return [CommentPublic(**row) for row in rows]


# Delete comment - only author of comment
@app.delete("/api/v1/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int, current_user: UserInDB = Depends(get_current_user)):
    comment = await db.fetchrow("SELECT author_id FROM comments WHERE id = $1", comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment["author_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    await db.execute("DELETE FROM comments WHERE id = $1", comment_id)
    return


# --- STARTUP & SHUTDOWN EVENTS ---

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


# --- RUNNER ---

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

```

```sql
-- Database schema: for PostgreSQL

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Posts Table
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Comments Table
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Indexes to optimize lookups
CREATE INDEX IF NOT EXISTS idx_posts_author_id ON posts(author_id);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_author_id ON comments(author_id);
```
