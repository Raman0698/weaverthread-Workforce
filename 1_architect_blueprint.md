# Gym Registration System — Technical Specification

## Overview
This document defines the technical specification for the Gym Registration System frontend and backend API contract. The primary goal is to ensure seamless integration between the frontend (registration UI) and backend services, with clear definitions for mandatory HTML element IDs and API endpoints.

---

## 1. Frontend Specification

### 1.1 Registration UI Components

| Element                    | Type            | Mandatory ID          | Description                          |
|----------------------------|-----------------|----------------------|------------------------------------|
| Register Toggle Button      | Button (Toggle) | `btnShowRegister`    | Button to reveal the registration form |
| Registration Email Input    | Input (email)   | `registerEmail`      | Input field for user's email address |
| Registration Username Input | Input (text)    | `registerUsername`   | Input field for user's chosen username |
| Registration Password Input | Input (password)| `registerPassword`   | Input field for user's password |

### 1.2 UI Behavior

- By default, the registration form is hidden.
- Clicking the button with ID `btnShowRegister` toggles the visibility of the registration form.
- The registration form contains the input fields with mandatory IDs `registerEmail`, `registerUsername`, and `registerPassword`.
- All inputs must validate user input on the client side for format and minimum requirements before submission.
- All validation errors should be clearly presented adjacent to the corresponding input field.

---

## 2. API Specification

### 2.1 Endpoint: Register User

| Property       | Value                      |
|----------------|----------------------------|
| URL            | `/api/register`             |
| Method         | POST                       |
| Content-Type   | `application/json`         |
| Authentication | None required for registration |

### 2.2 Request Payload

```json
{
  "email": "user@example.com",
  "username": "chosenUsername",
  "password": "securePassword123"
}
```

### 2.3 Response Payload

- **Success (201 Created):**

```json
{
  "message": "User registered successfully",
  "userId": "uniqueUserId123"
}
```

- **Error (400 Bad Request):**

```json
{
  "error": "Detailed error message explaining the validation failure"
}
```

---

## 3. Validation Rules

| Field              | Rules                                      | Notes                        |
|--------------------|--------------------------------------------|------------------------------|
| Email              | Must be a valid email format                | Standard RFC 5322 compliant   |
| Username           | 3-20 characters, alphanumeric and underscores | No spaces or special chars   |
| Password           | Minimum 8 characters, at least one uppercase, one lowercase, one digit, and one special character | Enforced on both client & server |

---

## 4. Security Considerations

- Passwords must be sent over HTTPS only.
- Passwords must never be logged or sent back in any response.
- Backend must hash and salt passwords securely before storage.
- Rate limiting to prevent brute-force attacks.
- CORS policies configured to accept requests from trusted origins only.

---

## 5. Summary of Mandatory HTML IDs

| ID                 | Element                 | Purpose                          |
|--------------------|-------------------------|---------------------------------|
| `btnShowRegister`  | Register toggle button   | Used to show/hide registration form |
| `registerEmail`    | Email input field        | User email input                |
| `registerUsername` | Username input field     | User username input             |
| `registerPassword` | Password input field     | User password input             |

---

## 6. Notes to Frontend and SDET Teams

- The frontend team **must ensure** the IDs listed above are used precisely to avoid automation and integration issues.
- SDET team should create automated tests targeting elements by these IDs.
- Any changes to the IDs must be approved and documented in this specification before implementation.

---

# End of Document