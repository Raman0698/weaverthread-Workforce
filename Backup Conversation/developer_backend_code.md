```sql
-- PostgreSQL schema for Gym Management Backend

-- Enable required extensions if needed (e.g., for UUID or others)
-- Not specified here since we use SERIAL

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE memberships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    membership_type VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_memberships_user_id ON memberships(user_id);

CREATE TABLE classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    instructor VARCHAR(255),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    booking_date TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'booked',
    CONSTRAINT unique_user_class_booking UNIQUE(user_id, class_id)
);

CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_class_id ON bookings(class_id);

-- Optional: roles and user_roles tables for extensibility

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
```

```python
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from sqlalchemy import (create_engine, Column, Integer, String, Boolean,
                        DateTime, Date, ForeignKey, Text, func, and_)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from starlette.requests import Request

# Configuration (normally from env vars)
DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/gymdb"
JWT_SECRET_KEY = "supersecretkey"  # use env var in prod!
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Database setup
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Models


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("Role", secondary="user_roles", back_populates="users")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    membership_type = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="memberships")


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    instructor = Column(String(255))
    capacity = Column(Integer, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    bookings = relationship("Booking", back_populates="gym_class", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(50), nullable=False, default='booked')

    user = relationship("User", back_populates="bookings")
    gym_class = relationship("Class", back_populates="bookings")

    __table_args__ = (
        # Unique constraint on (user_id, class_id) to prevent double booking
        # Will be enforced at DB level
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    users = relationship("User", secondary="user_roles", back_populates="roles")


from sqlalchemy import Table
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

# Pydantic Schemas


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: constr(min_length=8)


class UserRead(UserBase):
    id: int
    is_active: bool
    is_admin: bool

    class Config:
        orm_mode = True


class MembershipBase(BaseModel):
    membership_type: str
    start_date: date
    end_date: date


class MembershipCreate(MembershipBase):
    pass


class MembershipUpdate(BaseModel):
    membership_type: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[str]


class MembershipRead(MembershipBase):
    id: int
    user_id: int
    status: str

    class Config:
        orm_mode = True


class ClassBase(BaseModel):
    name: str
    description: Optional[str] = None
    instructor: Optional[str] = None
    capacity: int
    start_time: datetime
    end_time: datetime


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    instructor: Optional[str]
    capacity: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]


class ClassRead(ClassBase):
    id: int

    class Config:
        orm_mode = True


class BookingBase(BaseModel):
    class_id: int


class BookingCreate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: int
    user_id: int
    booking_date: datetime
    status: str

    class Config:
        orm_mode = True

# Security and Authentication Setup

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

app = FastAPI(title="Gym Management Backend")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency to get current user from token


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


# Authentication Routes


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    user_exists = db.query(User).filter(User.email == user_create.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user_create.password)
    user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        full_name=user_create.full_name,
        is_active=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# Membership Management


@app.get("/memberships/", response_model=List[MembershipRead])
def list_memberships(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    memberships = db.query(Membership).filter(Membership.user_id == current_user.id).all()
    return memberships


@app.post("/memberships/", response_model=MembershipRead, status_code=status.HTTP_201_CREATED)
def create_membership(membership_in: MembershipCreate,
                      current_user: User = Depends(get_current_active_user),
                      db: Session = Depends(get_db)):
    membership = Membership(
        user_id=current_user.id,
        membership_type=membership_in.membership_type,
        start_date=membership_in.start_date,
        end_date=membership_in.end_date,
        status="active"
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@app.put("/memberships/{membership_id}", response_model=MembershipRead)
def update_membership(membership_id: int,
                      membership_update: MembershipUpdate,
                      current_user: User = Depends(get_current_active_user),
                      db: Session = Depends(get_db)):
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    # Only admin or owner can update
    if not (current_user.is_admin or membership.user_id == current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    for attr, value in membership_update.dict(exclude_unset=True).items():
        setattr(membership, attr, value)

    membership.updated_at = datetime.utcnow()
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@app.delete("/memberships/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(membership_id: int,
                      current_user: User = Depends(get_current_active_user),
                      db: Session = Depends(get_db)):
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    if not (current_user.is_admin or membership.user_id == current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    db.delete(membership)
    db.commit()
    return None


# Class Management


@app.get("/classes/", response_model=List[ClassRead])
def list_upcoming_classes(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    classes = db.query(Class).filter(Class.start_time > now).order_by(Class.start_time).all()
    return classes


@app.get("/classes/{class_id}", response_model=ClassRead)
def get_class(class_id: int, db: Session = Depends(get_db)):
    gym_class = db.query(Class).filter(Class.id == class_id).first()
    if not gym_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return gym_class


@app.post("/classes/", response_model=ClassRead, status_code=status.HTTP_201_CREATED)
def create_class(class_in: ClassCreate,
                 current_user: User = Depends(require_admin),
                 db: Session = Depends(get_db)):
    gym_class = Class(
        name=class_in.name,
        description=class_in.description,
        instructor=class_in.instructor,
        capacity=class_in.capacity,
        start_time=class_in.start_time,
        end_time=class_in.end_time
    )
    db.add(gym_class)
    db.commit()
    db.refresh(gym_class)
    return gym_class


@app.put("/classes/{class_id}", response_model=ClassRead)
def update_class(class_id: int,
                 class_update: ClassUpdate,
                 current_user: User = Depends(require_admin),
                 db: Session = Depends(get_db)):
    gym_class = db.query(Class).filter(Class.id == class_id).first()
    if not gym_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    for attr, value in class_update.dict(exclude_unset=True).items():
        setattr(gym_class, attr, value)

    gym_class.updated_at = datetime.utcnow()
    db.add(gym_class)
    db.commit()
    db.refresh(gym_class)
    return gym_class


@app.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(class_id: int,
                 current_user: User = Depends(require_admin),
                 db: Session = Depends(get_db)):
    gym_class = db.query(Class).filter(Class.id == class_id).first()
    if not gym_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    db.delete(gym_class)
    db.commit()
    return None


# Booking Management


@app.get("/bookings/", response_model=List[BookingRead])
def list_bookings(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    return bookings


@app.post("/bookings/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(booking_in: BookingCreate,
                   current_user: User = Depends(get_current_active_user),
                   db: Session = Depends(get_db)):
    gym_class = db.query(Class).filter(Class.id == booking_in.class_id).first()
    if not gym_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # Check if class has capacity
    active_bookings_count = db.query(Booking).filter(
        Booking.class_id == booking_in.class_id,
        Booking.status == 'booked'
    ).count()
    if active_bookings_count >= gym_class.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Class is full")

    # Check for double booking (unique constraint handled by db, but check here also)
    existing_booking = db.query(Booking).filter(
        Booking.user_id == current_user.id,
        Booking.class_id == booking_in.class_id,
        Booking.status == 'booked'
    ).first()
    if existing_booking:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already booked this class")

    booking = Booking(
        user_id=current_user.id,
        class_id=booking_in.class_id,
        status='booked'
    )
    db.add(booking)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create booking")
    db.refresh(booking)
    return booking


@app.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(booking_id: int,
                   current_user: User = Depends(get_current_active_user),
                   db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # We delete the booking record to cancel; alternatively, could update status='cancelled'
    db.delete(booking)
    db.commit()
    return None
```