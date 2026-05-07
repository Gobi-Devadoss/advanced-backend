# 🏥 Advanced Hospital Management API

Production-ready backend application built using FastAPI with clean architecture, JWT authentication, RBAC, appointment management, file uploads, background tasks, and unit testing.


## 📌 Features
# 🔐 Authentication

-JWT Authentication (Access + Refresh Tokens)
-Secure Password Hashing using bcrypt
-Login & Registration
-Forgot Password (Token-Based Reset).

# 👥 Role-Based Access Control (RBAC)

Supported Roles:
-Admin
-Doctor
-Patient
Protected APIs using dependency-based authorization.
# 📅 Appointment Management

-Book appointments
-Prevent double booking
-Validate appointment slots
-Appointment status flow:
        -Pending
        -Approved
        -Rejected
        -Completed

# Search & Filtering
**Doctors**
-Search by name
-Search by specialization
**Appointments**
Filter by:
-Date
-Status
-Doctor
-Patient

# 📄 Pagination & Sorting
Supported in all listing APIs:
-page
-limit
-sort_by
-order (asc/desc)

# 📁 File Upload Handling
-File type validation
-File size validation
-Metadata storage in database

# ⚙️ Background Tasks
Uses FastAPI BackgroundTasks for:
-Mock email sending
-Async notifications

# ⚡ Caching
-Optional Redis/In-memory caching
-Cached doctor listing APIs

# 🚨 Error Handling
-Centralized exception handling
-Standard API response format

Example:
{
  "success": true,
  "message": "Appointment created successfully",
  "data": {},
  "error": null
}

# 🧠 Tech Stack
**Backend**
FastAPI
SQLAlchemy
Pydantic
JWT
Passlib (bcrypt)

**Database**
SQLite / PostgreSQL

**Testing**
Pytest

# 📁 Project Structure

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── security.py
│   ├── dependencies.py
│   └── exceptions.py
├── db/
│   ├── base.py
│   ├── session.py
│   └── init_db.py
├── models/
├── schemas/
├── routers/
├── services/
├── utils/
└── tests/
```
# ⚙️Installation

# Clone Repository
git clone <Gobi-Devadoss/advanced-backend>
cd hospital-management-api

# Create Virtual Environment

Windows
python -m venv .venv
.venv\Scripts\activate

Linox/mac
python3 -m venv .venv
source .venv/bin/activate

# Install Dependencies

pip install -r requirements.txt

🔑 Environment Variables

# Create .env file:

DATABASE_URL=sqlite:///./hospital.db
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ▶️ Run Server
uvicorn app.main:app --reload

Server runs at:

http://127.0.0.1:8000

Swagger Docs:

http://127.0.0.1:8000/docs

# 🔐 Authentication APIs
Register
POST /auth/register
Login
POST /auth/login
Forgot Password
POST /auth/forgot-password
Reset Password
POST /auth/reset-password
👨‍⚕️ Doctor APIs
Get Doctors
GET /doctors
Query Parameters
page
limit
specialization
search

# 📅 Appointment APIs
Create Appointment
POST /appointments
Get Appointments
GET /appointments
Update Appointment Status
PATCH /appointments/{id}

# 📁 File Upload API
Upload File
POST /files/upload

# Supported:

PNG
JPG
JPEG
PDF

# 🧪 Running Tests

pytest
📌 Example API Response
Success
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "jwt_token"
  },
  "error": null
}
Error
{
  "success": false,
  "message": "Invalid credentials",
  "data": null,
  "error": "Authentication failed"
}

# 🔒 Security Features
Password hashing with bcrypt
JWT authentication
Protected routes
Role-based authorization
Input validation using Pydantic

# 🧱 Architecture Highlights

✅ Clean Architecture
✅ Service Layer Pattern
✅ Modular Codebase
✅ Dependency Injection
✅ Scalable Structure
✅ Production-Oriented Design
