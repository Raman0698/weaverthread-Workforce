```sql
-- 1. Database Schema for Gym Membership Management System (Updated)

-- Enable necessary PostgreSQL extensions if required
-- (none specifically required for this schema)

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'staff', 'member')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index on username and email for faster lookups (done by UNIQUE constraints)

-- Membership Plans Table
CREATE TABLE membership_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    duration_months INT NOT NULL CHECK (duration_months > 0)
);

-- Memberships Table (added updated_at column)
CREATE TABLE memberships (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INT NOT NULL REFERENCES membership_plans(id) ON DELETE RESTRICT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'expired', 'cancelled', 'pending')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT memberships_valid_dates CHECK (end_date > start_date)
);

-- Indexes on memberships for commonly filtered columns
CREATE INDEX idx_memberships_user_id ON memberships(user_id);
CREATE INDEX idx_memberships_plan_id ON memberships(plan_id);
CREATE INDEX idx_memberships_status ON memberships(status);

-- Audit Logs Table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details JSONB
);

-- Index on timestamp for log queries
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
```

```python
import os
import enum
from datetime import datetime, timedelta, date
from typing import Optional, List

from fastapi import (
    FastAPI, Depends, HTTPException, status, Security
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Text, JSON, CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# ===================================================================
# Environment variables - JWT_SECRET_KEY is mandatory with no default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/gymdb")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is not set! This is required for security.")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# For CORS, set allowed origins securely via env or hardcode here for production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "")  # Comma separated list of allowed origins
if ALLOWED_ORIGINS:
    allowed_origins_list = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]
else:
    allowed_origins_list = []

# ===================================================================
# SQLAlchemy Base and Async Session Setup

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=False, future=True, pool_size=20, max_overflow=10)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ===================================================================
# Enum definitions for roles and membership statuses

class RoleEnum(str, enum.Enum):
    admin = "admin"
    staff = "staff"
    member = "member"


class MembershipStatusEnum(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"
    pending = "pending"


# ===================================================================
# SQLAlchemy Models

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # Enforced enum by CHECK constraint in DB
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    memberships = relationship("Membership", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    duration_months = Column(Integer, nullable=False)

    memberships = relationship("Membership", back_populates="plan")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint('end_date > start_date', name='memberships_valid_dates'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("membership_plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="memberships")
    plan = relationship("MembershipPlan", back_populates="memberships")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    details = Column(JSON, nullable=True)

    user = relationship("User", back_populates="audit_logs")


# ===================================================================
# Pydantic Schemas

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: constr(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True


class MembershipPlanBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    description: Optional[str]
    price: float
    duration_months: int


class MembershipPlanCreate(MembershipPlanBase):
    pass


class MembershipPlanUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)]
    description: Optional[str]
    price: Optional[float]
    duration_months: Optional[int]


class MembershipPlanResponse(MembershipPlanBase):
    id: int

    class Config:
        orm_mode = True


class MembershipBase(BaseModel):
    user_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: MembershipStatusEnum


class MembershipCreate(MembershipBase):
    pass


class MembershipUpdate(BaseModel):
    plan_id: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[MembershipStatusEnum]


class MembershipResponse(MembershipBase):
    id: int

    class Config:
        orm_mode = True


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    timestamp: datetime
    details: Optional[dict]

    class Config:
        orm_mode = True


# ===================================================================
# Security utils

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    q = select(User).where(User.username == username)
    result = await db.execute(q)
    return result.scalars().first()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception

    user = await get_user_by_username(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user


def role_checker(*allowed_roles: str):
    async def checker(current_user: User = Security(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return checker


# ===================================================================
# FastAPI app init and middlewares

app = FastAPI(title="Gym Membership Management API", version="1.0.0")

# CORS middleware with restricted origins
if allowed_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # No allowed origins provided, raise warning or block
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# HTTPS redirect middleware (enforced only if running without a proxy terminating HTTPS)
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)  # will redirect HTTP->HTTPS, requires HTTPS support

# ===================================================================
# Helper to create audit log entries


async def create_audit_log(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    details: Optional[dict] = None
):
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(log_entry)
    await db.commit()


# ===================================================================
# Routes - Authentication

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check username uniqueness
    existing_user = await get_user_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Check email uniqueness
    q = select(User).where(User.email == user_in.email)
    r = await db.execute(q)
    if r.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_in.password)

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        role=RoleEnum.member.value  # default role is member
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error during registration")
    await db.refresh(new_user)

    # Audit log
    await create_audit_log(db, new_user.id, "user_registered", {"username": new_user.username})

    return new_user


@app.post("/auth/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    # Audit log
    await create_audit_log(db, user.id, "user_login", {"username": user.username})

    return {"access_token": access_token, "token_type": "bearer"}


# ===================================================================
# Membership Plan CRUD endpoints

@app.post(
    "/plans",
    response_model=MembershipPlanResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["membership_plans"],
)
async def create_membership_plan(
    plan_in: MembershipPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value, RoleEnum.staff.value))
):
    plan = MembershipPlan(
        name=plan_in.name,
        description=plan_in.description,
        price=plan_in.price,
        duration_months=plan_in.duration_months
    )
    db.add(plan)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Plan name already exists")
    await db.refresh(plan)

    # Audit log
    await create_audit_log(
        db,
        current_user.id,
        "membership_plan_created",
        {"plan_id": plan.id, "name": plan.name}
    )

    return plan


@app.get(
    "/plans",
    response_model=List[MembershipPlanResponse],
    tags=["membership_plans"],
)
async def list_membership_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value, RoleEnum.staff.value, RoleEnum.member.value))
):
    q = select(MembershipPlan)
    result = await db.execute(q)
    return result.scalars().all()


@app.get(
    "/plans/{plan_id}",
    response_model=MembershipPlanResponse,
    tags=["membership_plans"],
)
async def get_membership_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value, RoleEnum.staff.value, RoleEnum.member.value))
):
    plan = await db.get(MembershipPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")
    return plan


@app.put(
    "/plans/{plan_id}",
    response_model=MembershipPlanResponse,
    tags=["membership_plans"],
)
async def update_membership_plan(
    plan_id: int,
    plan_in: MembershipPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value, RoleEnum.staff.value))
):
    plan = await db.get(MembershipPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    update_data = plan_in.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(plan, key, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error updating membership plan")

    await db.refresh(plan)

    # Audit log
    await create_audit_log(
        db,
        current_user.id,
        "membership_plan_updated",
        {"plan_id": plan.id, "updated_fields": list(update_data.keys())}
    )

    return plan


@app.delete(
    "/plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["membership_plans"],
)
async def delete_membership_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value))
):
    plan = await db.get(MembershipPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    await db.delete(plan)
    await db.commit()

    # Audit log
    await create_audit_log(
        db,
        current_user.id,
        "membership_plan_deleted",
        {"plan_id": plan_id}
    )
    return


# ===================================================================
# Memberships CRUD endpoints (single versions with audit logs and explicit current_user)

@app.get(
    "/memberships",
    response_model=List[MembershipResponse],
    tags=["memberships"],
)
async def list_memberships(
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value, RoleEnum.staff.value))
):
    q = select(Membership)
    result = await db.execute(q)
    return result.scalars().all()


@app.get(
    "/memberships/{membership_id}",
    response_model=MembershipResponse,
    tags=["memberships"],
)
async def get_membership(
    membership_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value, RoleEnum.staff.value, RoleEnum.member.value))
):
    membership = await db.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    # Allow members to see only their own memberships
    if current_user.role == RoleEnum.member.value and membership.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return membership


@app.get(
    "/memberships/me",
    response_model=List[MembershipResponse],
    tags=["memberships"],
)
async def get_current_user_memberships(
    current_user: User = Security(role_checker(RoleEnum.member.value, RoleEnum.staff.value, RoleEnum.admin.value)),
    db: AsyncSession = Depends(get_db)
):
    q = select(Membership).where(Membership.user_id == current_user.id)
    result = await db.execute(q)
    return result.scalars().all()


@app.post(
    "/memberships",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["memberships"],
)
async def create_membership(
    membership_in: MembershipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value, RoleEnum.staff.value))
):
    # Validate user exists
    user = await db.get(User, membership_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate plan exists
    plan = await db.get(MembershipPlan, membership_in.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    # Validate dates
    if membership_in.end_date <= membership_in.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    # Pydantic already validates status enum, double check redundant but safe
    if membership_in.status not in MembershipStatusEnum._value2member_map_:
        raise HTTPException(status_code=400, detail="Invalid status")

    membership = Membership(
        user_id=membership_in.user_id,
        plan_id=membership_in.plan_id,
        start_date=membership_in.start_date,
        end_date=membership_in.end_date,
        status=membership_in.status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)

    # Audit log
    await create_audit_log(
        db,
        current_user.id,
        "membership_created",
        {"membership_id": membership.id, "created_for_user_id": membership.user_id}
    )
    return membership


@app.put(
    "/memberships/{membership_id}",
    response_model=MembershipResponse,
    tags=["memberships"],
)
async def update_membership(
    membership_id: int,
    membership_in: MembershipUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value, RoleEnum.staff.value))
):
    membership = await db.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    update_data = membership_in.dict(exclude_unset=True)

    # Validate plan_id if given
    if "plan_id" in update_data:
        plan = await db.get(MembershipPlan, update_data["plan_id"])
        if not plan:
            raise HTTPException(status_code=404, detail="Membership plan not found")

    # Validate dates
    start_date = update_data.get("start_date", membership.start_date)
    end_date = update_data.get("end_date", membership.end_date)
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    # Validate status if given
    if "status" in update_data:
        if update_data["status"] not in MembershipStatusEnum._value2member_map_:
            raise HTTPException(status_code=400, detail="Invalid status")

    for key, value in update_data.items():
        setattr(membership, key, value)

    membership.updated_at = datetime.utcnow()

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error updating membership")

    await db.refresh(membership)

    # Audit log
    await create_audit_log(
        db,
        current_user.id,
        "membership_updated",
        {"membership_id": membership.id, "updated_fields": list(update_data.keys())}
    )
    return membership


@app.delete(
    "/memberships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["memberships"],
)
async def delete_membership(
    membership_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(role_checker(RoleEnum.admin.value))
):
    membership = await db.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    await db.delete(membership)
    await db.commit()

    # Audit log
    await create_audit_log(
        db,
        current_user.id,
        "membership_deleted",
        {"membership_id": membership_id}
    )
    return


# ===================================================================
# Root endpoint

@app.get("/")
async def root():
    return {"message": "Welcome to Gym Membership Management API"}


# ===================================================================
# Optional: Add logging configuration for app logs

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)

logger = logging.getLogger("gym_backend")

# Example usage:
# logger.info("Application started")

# ===================================================================
# Notes:
# - Alembic migration scripts are required to apply these DB updates.
# - Password policy can be enhanced with custom validator if desired.
# - HTTPS enforcement middleware requires HTTPS support on server.
# - Token revocation is not implemented; users must wait for token expiration.
# - CORS origins must be configured via ALLOWED_ORIGINS env var in production.

```
