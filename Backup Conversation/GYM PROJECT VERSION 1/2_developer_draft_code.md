```sql
-- PostgreSQL Database Schema for Local Gym Membership Management

CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE membership_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    duration_days INTEGER NOT NULL,
    price NUMERIC(10, 2),
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE memberships (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES membership_plans(id) ON DELETE RESTRICT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('active', 'expired', 'paused'))
);

CREATE TABLE classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    trainer VARCHAR(255),
    schedule TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    booking_time TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

```python
from datetime import datetime, timedelta, date
from typing import List, Optional

import bcrypt
import jwt
from fastapi import (
    FastAPI, Depends, HTTPException, status, Security, Body, Path, Query
)
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, constr, validator
from sqlalchemy import (
    Column, String, Integer, Boolean, Date, DateTime, Numeric, ForeignKey, Enum, select, func, and_
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.exc import NoResultFound
import enum
import os

# --- Settings and Configuration ---

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/gymdb")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")  # Use secure env var in production
JWT_ALGORITHM = "HS256"

# --- Database setup ---

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

# --- Models for SQLAlchemy ---

class MembershipStatusEnum(str, enum.Enum):
    active = "active"
    expired = "expired"
    paused = "paused"


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    memberships = relationship("Membership", back_populates="member", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="member", cascade="all, delete-orphan")


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    duration_days = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    memberships = relationship("Membership", back_populates="plan", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("membership_plans.id", ondelete="RESTRICT"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(10), nullable=False)  # 'active', 'expired', 'paused'

    member = relationship("Member", back_populates="memberships")
    plan = relationship("MembershipPlan", back_populates="memberships")


class GymClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    trainer = Column(String(255), nullable=True)
    schedule = Column(DateTime(timezone=True), nullable=False, index=True)

    bookings = relationship("Booking", back_populates="gym_class", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    booking_time = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    member = relationship("Member", back_populates="bookings")
    gym_class = relationship("GymClass", back_populates="bookings")

# --- Pydantic Schemas ---

# Auth schemas

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[int] = None

# Member schemas

class MemberBase(BaseModel):
    name: Optional[constr(strip_whitespace=True, max_length=255)]
    email: EmailStr
    phone: Optional[constr(strip_whitespace=True, max_length=50)]

class MemberCreate(MemberBase):
    password: constr(min_length=8)

class MemberUpdate(BaseModel):
    name: Optional[constr(strip_whitespace=True, max_length=255)]
    phone: Optional[constr(strip_whitespace=True, max_length=50)]

class MemberRead(MemberBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Membership Plan schemas

class MembershipPlanCreate(BaseModel):
    name: constr(strip_whitespace=True, max_length=255)
    duration_days: int
    price: Optional[float]
    active: Optional[bool] = True

    @validator('duration_days')
    def duration_positive(cls, v):
        if v <= 0:
            raise ValueError("duration_days must be positive")
        return v

class MembershipPlanUpdate(BaseModel):
    name: Optional[constr(strip_whitespace=True, max_length=255)]
    duration_days: Optional[int]
    price: Optional[float]
    active: Optional[bool]

class MembershipPlanRead(BaseModel):
    id: int
    name: str
    duration_days: int
    price: Optional[float]
    active: bool

    class Config:
        orm_mode = True

# Membership schemas

class MembershipCreate(BaseModel):
    member_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: constr(regex="^(active|expired|paused)$")

    @validator('end_date')
    def end_after_start(cls, v, values):
        start = values.get('start_date')
        if start and v < start:
            raise ValueError("end_date must be after start_date")
        return v

class MembershipUpdate(BaseModel):
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[constr(regex="^(active|expired|paused)$")]

    @validator('end_date')
    def end_after_start(cls, v, values):
        start = values.get('start_date')
        if v and start and v < start:
            raise ValueError("end_date must be after start_date")
        return v

class MembershipRead(BaseModel):
    id: int
    member_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: str

    class Config:
        orm_mode = True

# GymClass schemas

class GymClassCreate(BaseModel):
    name: Optional[constr(strip_whitespace=True, max_length=255)]
    trainer: Optional[constr(strip_whitespace=True, max_length=255)]
    schedule: datetime

class GymClassUpdate(BaseModel):
    name: Optional[constr(strip_whitespace=True, max_length=255)]
    trainer: Optional[constr(strip_whitespace=True, max_length=255)]
    schedule: Optional[datetime]

class GymClassRead(BaseModel):
    id: int
    name: Optional[str]
    trainer: Optional[str]
    schedule: datetime

    class Config:
        orm_mode = True

# Booking schemas

class BookingCreate(BaseModel):
    member_id: int
    class_id: int

class BookingRead(BaseModel):
    id: int
    member_id: int
    class_id: int
    booking_time: datetime

    class Config:
        orm_mode = True

# Password reset schema

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: constr(min_length=8)


# --- Utils ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode())

def create_access_token(subject: int, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": str(subject), "exp": expire}
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

async def get_member_by_email(session: AsyncSession, email: str) -> Optional[Member]:
    q = select(Member).where(Member.email == email)
    result = await session.execute(q)
    return result.scalars().first()

async def get_member_by_id(session: AsyncSession, member_id: int) -> Optional[Member]:
    q = select(Member).where(Member.id == member_id)
    result = await session.execute(q)
    return result.scalars().first()

async def get_current_member(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(async_session)
) -> Member:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        member_id: str = payload.get("sub")
        if member_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    member = await get_member_by_id(session, int(member_id))
    if member is None:
        raise credentials_exception
    return member

# --- FastAPI App and Routers ---

app = FastAPI(title="Local Gym Membership Management API")

# Dependency to get DB session in path operations

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


# --- AUTH ROUTER ---

from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    member = await get_member_by_email(session, form_data.username)
    if not member:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, member.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(subject=member.id)
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/password-reset-request", status_code=204)
async def password_reset_request(body: PasswordResetRequest, session: AsyncSession = Depends(get_db)):
    """
    This would normally send an email with a reset token.
    Here we simulate by generating a dummy token.
    """
    member = await get_member_by_email(session, body.email)
    if not member:
        # Do not reveal if email exists or not
        return
    # Generate reset token (in real: store in DB with expiration)
    reset_token = jwt.encode(
        {"sub": str(member.id), "exp": datetime.utcnow() + timedelta(hours=1)},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    # TODO: Send email with reset_token
    # For this implementation, assume email sent
    return

@auth_router.post("/password-reset-confirm", status_code=204)
async def password_reset_confirm(body: PasswordResetConfirm, session: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(body.token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        member_id = int(payload.get("sub"))
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    member = await get_member_by_id(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    new_hash = hash_password(body.new_password)
    member.password_hash = new_hash
    await session.commit()
    return


# --- MEMBERS ROUTER ---

members_router = APIRouter(prefix="/members", tags=["members"])

@members_router.post("/", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
async def create_member(
    member_in: MemberCreate,
    session: AsyncSession = Depends(get_db),
):
    existing = await get_member_by_email(session, member_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(member_in.password)
    new_member = Member(
        name=member_in.name,
        email=member_in.email,
        phone=member_in.phone,
        password_hash=hashed_password,
    )
    session.add(new_member)
    await session.commit()
    await session.refresh(new_member)
    return new_member

@members_router.get("/", response_model=List[MemberRead])
async def list_members(
    skip: int = 0,
    limit: int = 100,
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    # In real app, add permission checks
    q = select(Member).offset(skip).limit(limit)
    result = await session.execute(q)
    members = result.scalars().all()
    return members

@members_router.get("/{member_id}", response_model=MemberRead)
async def get_member(
    member_id: int = Path(..., gt=0),
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    member = await get_member_by_id(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    # Optional: restrict access so members can only see their own profile or admins can see all
    return member

@members_router.put("/{member_id}", response_model=MemberRead)
async def update_member(
    member_id: int = Path(..., gt=0),
    member_in: MemberUpdate = Body(...),
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    member = await get_member_by_id(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    # In real app, check permissions
    if member_in.name is not None:
        member.name = member_in.name
    if member_in.phone is not None:
        member.phone = member_in.phone
    await session.commit()
    await session.refresh(member)
    return member

@members_router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: int = Path(..., gt=0),
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    member = await get_member_by_id(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await session.delete(member)
    await session.commit()
    return


# --- MEMBERSHIP PLANS ROUTER ---

memberships_plan_router = APIRouter(prefix="/memberships", tags=["memberships"])

@memberships_plan_router.post("/plans", response_model=MembershipPlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_in: MembershipPlanCreate,
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    # For simplicity, anyone logged in can create plans; in real app, check admin permissions
    plan = MembershipPlan(
        name=plan_in.name,
        duration_days=plan_in.duration_days,
        price=plan_in.price,
        active=plan_in.active,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan

@memberships_plan_router.get("/plans", response_model=List[MembershipPlanRead])
async def list_plans(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    q = select(MembershipPlan).offset(skip).limit(limit)
    result = await session.execute(q)
    plans = result.scalars().all()
    return plans

@memberships_plan_router.get("/plans/{plan_id}", response_model=MembershipPlanRead)
async def get_plan(
    plan_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    plan = await session.get(MembershipPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")
    return plan

@memberships_plan_router.put("/plans/{plan_id}", response_model=MembershipPlanRead)
async def update_plan(
    plan_id: int = Path(..., gt=0),
    plan_in: MembershipPlanUpdate = Body(...),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    plan = await session.get(MembershipPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")
    if plan_in.name is not None:
        plan.name = plan_in.name
    if plan_in.duration_days is not None:
        if plan_in.duration_days <= 0:
            raise HTTPException(status_code=400, detail="duration_days must be positive")
        plan.duration_days = plan_in.duration_days
    if plan_in.price is not None:
        plan.price = plan_in.price
    if plan_in.active is not None:
        plan.active = plan_in.active
    await session.commit()
    await session.refresh(plan)
    return plan

@memberships_plan_router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def retire_plan(
    plan_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    plan = await session.get(MembershipPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")
    # We retire the plan by setting active=False, not deleting it to keep referential integrity
    plan.active = False
    await session.commit()
    return


# --- MEMBERSHIPS ASSIGNMENT ROUTER ---

@memberships_plan_router.post("/assign", response_model=MembershipRead, status_code=status.HTTP_201_CREATED)
async def assign_membership(
    membership_in: MembershipCreate,
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    # Validate member exists
    member = await get_member_by_id(session, membership_in.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    # Validate plan exists and active
    plan = await session.get(MembershipPlan, membership_in.plan_id)
    if not plan or not plan.active:
        raise HTTPException(status_code=404, detail="Active membership plan not found")
    if membership_in.end_date < membership_in.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    new_membership = Membership(
        member_id=membership_in.member_id,
        plan_id=membership_in.plan_id,
        start_date=membership_in.start_date,
        end_date=membership_in.end_date,
        status=membership_in.status,
    )
    session.add(new_membership)
    await session.commit()
    await session.refresh(new_membership)
    return new_membership

@memberships_plan_router.get("/member/{member_id}", response_model=List[MembershipRead])
async def get_memberships_by_member(
    member_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    memberships = await session.execute(
        select(Membership).where(Membership.member_id == member_id)
    )
    return memberships.scalars().all()

@memberships_plan_router.put("/{membership_id}", response_model=MembershipRead)
async def update_membership(
    membership_id: int = Path(..., gt=0),
    membership_update: MembershipUpdate = Body(...),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    membership = await session.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    if membership_update.start_date is not None:
        membership.start_date = membership_update.start_date
    if membership_update.end_date is not None:
        if membership_update.start_date and membership_update.end_date < membership_update.start_date:
            raise HTTPException(status_code=400, detail="end_date must be after start_date")
        if membership_update.end_date < membership.start_date:
            raise HTTPException(status_code=400, detail="end_date must be after start_date")
        membership.end_date = membership_update.end_date
    if membership_update.status is not None:
        if membership_update.status not in MembershipStatusEnum._value2member_map_:
            raise HTTPException(status_code=400, detail="Invalid status")
        membership.status = membership_update.status
    await session.commit()
    await session.refresh(membership)
    return membership

@memberships_plan_router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_membership(
    membership_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    membership = await session.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    await session.delete(membership)
    await session.commit()
    return

# --- CLASSES ROUTER ---

classes_router = APIRouter(prefix="/classes", tags=["classes"])

@classes_router.post("/", response_model=GymClassRead, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_in: GymClassCreate,
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    gym_class = GymClass(
        name=class_in.name,
        trainer=class_in.trainer,
        schedule=class_in.schedule,
    )
    session.add(gym_class)
    await session.commit()
    await session.refresh(gym_class)
    return gym_class

@classes_router.get("/", response_model=List[GymClassRead])
async def list_classes(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    q = select(GymClass).offset(skip).limit(limit).order_by(GymClass.schedule)
    result = await session.execute(q)
    classes = result.scalars().all()
    return classes

@classes_router.get("/{class_id}", response_model=GymClassRead)
async def get_class(
    class_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    gym_class = await session.get(GymClass, class_id)
    if not gym_class:
        raise HTTPException(status_code=404, detail="Class not found")
    return gym_class

@classes_router.put("/{class_id}", response_model=GymClassRead)
async def update_class(
    class_id: int = Path(..., gt=0),
    class_update: GymClassUpdate = Body(...),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    gym_class = await session.get(GymClass, class_id)
    if not gym_class:
        raise HTTPException(status_code=404, detail="Class not found")
    if class_update.name is not None:
        gym_class.name = class_update.name
    if class_update.trainer is not None:
        gym_class.trainer = class_update.trainer
    if class_update.schedule is not None:
        gym_class.schedule = class_update.schedule
    await session.commit()
    await session.refresh(gym_class)
    return gym_class

@classes_router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    gym_class = await session.get(GymClass, class_id)
    if not gym_class:
        raise HTTPException(status_code=404, detail="Class not found")
    await session.delete(gym_class)
    await session.commit()
    return

# --- BOOKINGS ROUTER ---

bookings_router = APIRouter(prefix="/bookings", tags=["bookings"])

@bookings_router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def book_class(
    booking_in: BookingCreate,
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    # Confirm member exists
    member = await get_member_by_id(session, booking_in.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    # Confirm class exists
    gym_class = await session.get(GymClass, booking_in.class_id)
    if not gym_class:
        raise HTTPException(status_code=404, detail="Class not found")

    # Optional: check class schedule is in future etc.
    booking = Booking(
        member_id=booking_in.member_id,
        class_id=booking_in.class_id,
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking

@bookings_router.get("/member/{member_id}", response_model=List[BookingRead])
async def get_member_bookings(
    member_id: int = Path(..., gt=0),
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    bookings = await session.execute(
        select(Booking).where(Booking.member_id == member_id).order_by(Booking.booking_time.desc())
    )
    return bookings.scalars().all()

@bookings_router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: int = Path(..., gt=0),
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    booking = await session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    # Optional: restrict so member can only cancel own bookings
    await session.delete(booking)
    await session.commit()
    return

# --- REPORTS ROUTER ---

reports_router = APIRouter(prefix="/reports", tags=["reports"])

@reports_router.get("/active-memberships", response_model=List[MembershipRead])
async def report_active_memberships(
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    today = date.today()
    q = select(Membership).where(
        and_(
            Membership.status == 'active',
            Membership.start_date <= today,
            Membership.end_date >= today,
        )
    )
    result = await session.execute(q)
    return result.scalars().all()

@reports_router.get("/attendance/member/{member_id}", response_model=List[BookingRead])
async def report_member_attendance(
    member_id: int = Path(..., gt=0),
    current_member: Member = Depends(get_current_member),
    session: AsyncSession = Depends(get_db),
):
    # Return bookings as proxy for attendance
    bookings = await session.execute(
        select(Booking).where(Booking.member_id == member_id).order_by(Booking.booking_time.desc())
    )
    return bookings.scalars().all()

# --- Include routers ---

app.include_router(auth_router)
app.include_router(members_router)
app.include_router(memberships_plan_router)
app.include_router(classes_router)
app.include_router(bookings_router)
app.include_router(reports_router)

# --- Startup event: create tables ---

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```
