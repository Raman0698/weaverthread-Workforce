# Technical Specification Document

## Project Overview
Develop a secure backend system for a local gym to manage:
- Memberships
- Class bookings

The system will be built using FastAPI (Python) for the API layer and PostgreSQL as the relational database backend. The architecture will emphasize security, scalability, and maintainability.

---

## Architecture Overview

- **Backend Framework:** FastAPI
  - High-performance asynchronous capabilities
  - Type-safe data validation with Pydantic
  - Automatic OpenAPI schema generation for API documentation
  - Built-in support for OAuth2 with JWT for authentication

- **Database:** PostgreSQL
  - Use of relational tables with foreign keys, indices
  - ACID compliance for transactional integrity
  - Secure role-based access control on the database level

- **Security**
  - User authentication via OAuth2 Password flow with JWT token issuance
  - Password hashing with a strong algorithm (e.g., bcrypt or Argon2)
  - HTTPS deployment enforced in production (deployment not covered here)
  - Input validation through Pydantic models
  - Secure API routes through authentication and role-based checks

---

## Database Design

### Tables

1. **users**
   - `id` SERIAL PRIMARY KEY
   - `email` VARCHAR(255) UNIQUE NOT NULL
   - `hashed_password` VARCHAR(255) NOT NULL
   - `full_name` VARCHAR(255)
   - `is_active` BOOLEAN DEFAULT TRUE
   - `is_admin` BOOLEAN DEFAULT FALSE
   - `created_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   - `updated_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW()

2. **memberships**
   - `id` SERIAL PRIMARY KEY
   - `user_id` INTEGER REFERENCES users(id) ON DELETE CASCADE
   - `membership_type` VARCHAR(100) NOT NULL (e.g., monthly, yearly)
   - `start_date` DATE NOT NULL
   - `end_date` DATE NOT NULL
   - `status` VARCHAR(50) NOT NULL (e.g., active, expired, cancelled)
   - `created_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   - `updated_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW()

3. **classes**
   - `id` SERIAL PRIMARY KEY
   - `name` VARCHAR(255) NOT NULL
   - `description` TEXT
   - `instructor` VARCHAR(255)
   - `capacity` INTEGER NOT NULL
   - `start_time` TIMESTAMP WITH TIME ZONE NOT NULL
   - `end_time` TIMESTAMP WITH TIME ZONE NOT NULL
   - `created_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   - `updated_at` TIMESTAMP WITH TIME ZONE DEFAULT NOW()

4. **bookings**
   - `id` SERIAL PRIMARY KEY
   - `user_id` INTEGER REFERENCES users(id) ON DELETE CASCADE
   - `class_id` INTEGER REFERENCES classes(id) ON DELETE CASCADE
   - `booking_date` TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   - `status` VARCHAR(50) NOT NULL DEFAULT 'booked' (e.g., booked, cancelled)
   - **Unique constraint:** user_id + class_id to prevent double booking

5. **roles** (optional for extensibility)
   - `id` SERIAL PRIMARY KEY
   - `name` VARCHAR(50) UNIQUE NOT NULL
   - `description` TEXT

6. **user_roles** (optional many-to-many user-role relationship)
   - `user_id` INTEGER REFERENCES users(id) ON DELETE CASCADE
   - `role_id` INTEGER REFERENCES roles(id) ON DELETE CASCADE
   - **Primary key of (user_id, role_id)**

---

## API Routes

All endpoints assume HTTPS usage and token-based authentication with JWT.

### Authentication
- `POST /auth/register`
  - Register a new user (member)
  - Request body: email, password, full_name
  - Validation: email format, password complexity

- `POST /auth/login`
  - User login with email and password
  - Returns: JWT access token and token type

- `GET /auth/me`
  - Get current user profile
  - Protected route

### Membership Management
- `GET /memberships/`
  - List memberships for the authenticated user
  - Protected route

- `POST /memberships/`
  - Create (purchase) a new membership for the authenticated user
  - Request body: membership_type, start_date, end_date
  - Protected route

- `PUT /memberships/{membership_id}`
  - Update an existing membership (only admin or the owner)
  - Request body: membership attributes to update

- `DELETE /memberships/{membership_id}`
  - Cancel or delete a membership (only admin or the owner)

### Class Management
- `GET /classes/`
  - List all upcoming classes
  - Public route or optionally protected

- `GET /classes/{class_id}`
  - Get class detail

- `POST /classes/`
  - Create new class (admin only)
  - Request body: name, description, instructor, capacity, start_time, end_time

- `PUT /classes/{class_id}`
  - Update class details (admin only)

- `DELETE /classes/{class_id}`
  - Delete class (admin only)

### Booking Management
- `GET /bookings/`
  - List all bookings for authenticated user

- `POST /bookings/`
  - Create a booking for a class
  - Request body: class_id

- `DELETE /bookings/{booking_id}`
  - Cancel a booking

---

## Data Models (Pydantic Examples)

```python
from pydantic import BaseModel, EmailStr, constr
from datetime import date, datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str]

class UserCreate(UserBase):
    password: constr(min_length=8)  # enforce password rules

class User(UserBase):
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

class Membership(MembershipBase):
    id: int
    user_id: int
    status: str

    class Config:
        orm_mode = True

class ClassBase(BaseModel):
    name: str
    description: Optional[str]
    instructor: Optional[str]
    capacity: int
    start_time: datetime
    end_time: datetime

class ClassCreate(ClassBase):
    pass

class Class(ClassBase):
    id: int

    class Config:
        orm_mode = True

class BookingBase(BaseModel):
    class_id: int

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    user_id: int
    booking_date: datetime
    status: str

    class Config:
        orm_mode = True
```

---

## Security Considerations

- Passwords stored as salted hashes using a strong algorithm.
- Use FastAPI's `Security` utilities to implement OAuth2 with password and JWT bearer tokens.
- Access control to routes:
  - Admin-only routes guarded by role verification.
  - Member routes access only their own data.
- Rate limiting and request throttling to prevent brute force (to be implemented during deployment or via proxy).
- Input validation and sanitization to prevent injection attacks.

---

## Deployment Notes

- Deploy FastAPI with ASGI server like Uvicorn or Hypercorn with appropriate worker settings.
- Use environment variables or secret management tools for database credentials, JWT secret keys, and other sensitive configs.
- Enable HTTPS with valid certificates.
- Maintain database migrations with Alembic or similar tools.

---

This specification provides a secure, scalable backend architecture to manage gym memberships and class bookings with clear separation of responsibilities, proper authentication, and relational data design for future extensibility.