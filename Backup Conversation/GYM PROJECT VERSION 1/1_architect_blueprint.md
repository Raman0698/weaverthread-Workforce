# Technical Specification Document

## Project Overview

### Purpose
This document specifies the technical requirements, API contract, and architectural blueprint for developing a secure backend system and a clean frontend user interface for a local gym. The system will facilitate user registrations, management, and related functionalities in a secure, user-friendly manner.

### Scope
- Backend: Secure, RESTful API services for user registration, authentication, and management.
- Frontend: Responsive UI for user registration and administrative management.
- Security: Proper authentication, authorization, input validation, and data protection.
- Technology Stack: 
  - Backend API: FastAPI (Python) 
  - Database: PostgreSQL
  - Frontend: React or similar with TailwindCSS for styling

---

## System Architecture and Design

### Backend Architecture
- Framework: FastAPI (for asynchronous, high-performance API)
- Database: PostgreSQL (Relational DB for structured user data)
- Authentication: JWT (JSON Web Tokens) for stateless, secure authentication
- Passwords: Hashed with bcrypt or Argon2
- API Type: RESTful with JSON payloads

### Frontend Architecture
- Framework: React (component-based, reusable UI)
- Styling: TailwindCSS for rapid, clean frontend design
- State Management: React Context or Redux as needed
- Authentication: Store JWT tokens in secure HTTP-only cookies or memory

---

## Functional Requirements

### User Registration
- Users can register by providing:
  - Full name
  - Email address (unique)
  - Password (with strength validation)
  - Phone number (optional)
  - Date of birth (optional)
- Backend validation to prevent duplicate emails

### User Authentication
- Login with email and password
- Generate JWT access tokens
- Secure token storage and expiration
- Password reset via email (optional / future)

### User Management
- Admin endpoints for:
  - Listing all users (pagination)
  - Viewing user details
  - Updating user information
  - Deleting users

---

## Non-Functional Requirements

- Secure transmission: HTTPS mandatory
- Password security: salted and hashed
- Input validation on backend & frontend
- API rate limiting (optional/future)
- Proper error handling and consistent response structure
- GDPR compliance concerning user data (privacy)

---

## API Contract Specification

Base URL: `/api/v1`

---

### 1. User Registration

**POST** `/users/register`

Request Body (application/json):
```json
{
  "full_name": "string",
  "email": "string",
  "password": "string",
  "phone": "string (optional)",
  "date_of_birth": "YYYY-MM-DD (optional)"
}
```

Response Success (201 Created):
```json
{
  "id": "uuid",
  "full_name": "string",
  "email": "string",
  "phone": "string | null",
  "date_of_birth": "YYYY-MM-DD | null",
  "created_at": "ISO 8601 datetime string"
}
```

Response Errors:
- 400 Bad Request: Invalid input or missing fields
- 409 Conflict: Email already exists

---

### 2. User Login

**POST** `/auth/login`

Request Body:
```json
{
  "email": "string",
  "password": "string"
}
```

Response Success (200 OK):
```json
{
  "access_token": "string (JWT token)",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Response Errors:
- 400 Bad Request: Missing fields
- 401 Unauthorized: Invalid credentials

---

### 3. Get Current User Profile

**GET** `/users/me`

Headers:
```
Authorization: Bearer <access_token>
```

Response Success (200 OK):
```json
{
  "id": "uuid",
  "full_name": "string",
  "email": "string",
  "phone": "string | null",
  "date_of_birth": "YYYY-MM-DD | null",
  "created_at": "ISO 8601 datetime string"
}
```

Response Errors:
- 401 Unauthorized: Missing or invalid token

---

### 4. Admin: List Users

**GET** `/admin/users`

Headers:
```
Authorization: Bearer <access_token>
```

Query Parameters:
- `page`: integer (default 1)
- `page_size`: integer (default 20, max 100)

Response Success (200 OK):
```json
{
  "users": [
    {
      "id": "uuid",
      "full_name": "string",
      "email": "string",
      "phone": "string | null",
      "date_of_birth": "YYYY-MM-DD | null",
      "created_at": "ISO 8601 datetime string"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

Response Errors:
- 401 Unauthorized: Token missing/invalid or user not admin

---

### 5. Admin: Get User Details

**GET** `/admin/users/{user_id}`

Headers:
```
Authorization: Bearer <access_token>
```

Path Parameter:
- `user_id`: uuid

Response Success (200 OK):
```json
{
  "id": "uuid",
  "full_name": "string",
  "email": "string",
  "phone": "string | null",
  "date_of_birth": "YYYY-MM-DD | null",
  "created_at": "ISO 8601 datetime string"
}
```

Response Errors:
- 401 Unauthorized: Token missing/invalid or user not admin
- 404 Not Found: User not found

---

### 6. Admin: Update User

**PUT** `/admin/users/{user_id}`

Headers:
```
Authorization: Bearer <access_token>
```

Path Parameter:
- `user_id`: uuid

Request Body (application/json) - All fields optional but at least one required:
```json
{
  "full_name": "string (optional)",
  "email": "string (optional)",
  "phone": "string (optional)",
  "date_of_birth": "YYYY-MM-DD (optional)"
}
```

Response Success (200 OK):
```json
{
  "id": "uuid",
  "full_name": "string",
  "email": "string",
  "phone": "string | null",
  "date_of_birth": "YYYY-MM-DD | null",
  "created_at": "ISO 8601 datetime string"
}
```

Response Errors:
- 400 Bad Request: Invalid input
- 401 Unauthorized: Token missing/invalid or user not admin
- 404 Not Found: User not found
- 409 Conflict: Email already in use

---

### 7. Admin: Delete User

**DELETE** `/admin/users/{user_id}`

Headers:
```
Authorization: Bearer <access_token>
```

Path Parameter:
- `user_id`: uuid

Response Success (204 No Content)

Response Errors:
- 401 Unauthorized: Token missing/invalid or user not admin
- 404 Not Found: User not found

---

## Data Model (Simplified)

| Field         | Type        | Constraints                    |
|---------------|-------------|-------------------------------|
| id            | UUID        | Primary Key                   |
| full_name     | String      | Required                     |
| email         | String      | Required, Unique             |
| password_hash | String      | Required                     |
| phone         | String      | Optional                     |
| date_of_birth | Date        | Optional                     |
| created_at    | DateTime    | Auto-generated               |

---

## Security Considerations

- Passwords stored hashed with bcrypt/Argon2.
- JWT tokens signed with a strong secret key.
- Token expiration set to 1 hour, with refresh token strategy possible for extension.
- All API endpoints require HTTPS.
- Admin endpoints require admin claim in JWT.
- Input validations both client-side and server-side.
- Rate limiting to be considered for public endpoints.

---

## Frontend UI Recommendations

### User Registration Page
- Form fields as per registration API
- Password strength indicator
- Client-side validation for email and phone formats
- Successful registration redirect or confirmation message

### Login Page
- Email and password fields
- Show validation and error messages clearly

### User Profile Page
- Display user information with option to update (if applicable)

### Admin Dashboard
- Paginated user list view with search
- View, edit, delete users functionality with confirmation modals
- Access control (only visible to admin users)

Styling with TailwindCSS to ensure neat, responsive layouts.

---

## Next Steps / Additional Features

- Password reset via email.
- Role-based access control (extendable).
- Activity logs for admins.
- Analytics dashboard (optional).
- Mobile app integration.

---

# End of Document