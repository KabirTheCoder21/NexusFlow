# 🚀 Production Ready Task Management System API

A production-ready Task Management REST API built using **FastAPI**, **SQLAlchemy (Async)**, **PostgreSQL**, and **JWT Authentication** following clean architecture, security best practices, and scalable backend design.

This project demonstrates authentication, authorization, session management, role-based access control, soft delete, logging, and production-ready API development.

---

# ✨ Features

## Authentication & Authorization

- User Registration
- Secure Login
- JWT Access Token Authentication
- Refresh Token Support
- Session-based Authentication
- Logout
- Change Password
- Profile Management
- Role-Based Access Control (RBAC)

---

## User Features

- Register Account
- Login
- Refresh Access Token
- View Profile
- Update Profile
- Change Password
- Logout

---

## Task Management

- Create Task
- Get All Tasks
- Get Task By ID
- Update Task
- Update Task Status
- Soft Delete Task
- Recover Deleted Task

---

## Admin Features

- View All Users
- Dashboard Statistics
- Soft Delete Users
- Restore Users
- Update User Status
- Update User Role

---

# 🔐 Security Features

This project focuses heavily on security.

### Password Security

- Passwords hashed using bcrypt
- Password verification using secure hash comparison
- Password change requires old password verification

---

### JWT Authentication

- Access Token
- Refresh Token
- Token Expiration
- Token Validation

---

### Session Management

Unlike traditional JWT implementations, this project maintains a dedicated **User Session Table**.

Each successful login creates a new session.

Sessions are validated on every authenticated request.

This enables:

- Logout from current device
- Session Revocation
- Password Change Session Invalidation
- Future support for Login History
- Multi Device Sessions

---

### Password Change Security

Changing password automatically:

- Updates password hash
- Revokes all active sessions
- Forces user to login again

This prevents stolen JWT tokens from remaining valid.

---

### Soft Delete

Instead of permanently deleting records:

- Users are soft deleted
- Tasks are soft deleted

Deleted records can be restored.

---

### Authorization

Role Based Access Control

Current Roles:

- Admin
- User

Admin endpoints are protected using authorization dependencies.

---

# 🏗 Project Architecture

```
TECH_SIMPLUS/
│
├── alembic/                  # Database migration scripts
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── src/
│   │
│   ├── admin/                # Admin module
│   │   ├── controller.py
│   │   ├── dtos.py
│   │   └── router.py
│   │
│   ├── auth/                 # Authentication & Authorization
│   │   ├── dependencies.py
│   │   ├── dtos.py
│   │   ├── jwt_config.py
│   │   ├── models.py
│   │   ├── security.py
│   │   └── session_repository.py
│   │
│   ├── tasks/                # Task Management
│   │   ├── controller.py
│   │   ├── constant.py
│   │   ├── dtos.py
│   │   ├── enums.py
│   │   ├── models.py
│   │   └── router.py
│   │
│   ├── user/                 # User Management
│   │   ├── controller.py
│   │   ├── dtos.py
│   │   ├── enums.py
│   │   ├── models.py
│   │   └── router.py
│   │
│   └── utils/                # Shared utilities & helper functions
│
├── .env                      # Environment configuration
├── alembic.ini               # Alembic configuration
├── main.py                   # FastAPI application entry point
└── README.md
```

### Architecture Overview

The project follows a **feature-based modular architecture**, where each business domain (Authentication, Users, Tasks, and Admin) is organized into its own module. Each module encapsulates its routing, request/response DTOs, controllers, models, and business logic, making the application easier to maintain, extend, and scale.

Each module generally consists of:

- **router.py** – Defines API endpoints.
- **controller.py** – Contains business logic.
- **dtos.py** – Pydantic request/response schemas.
- **models.py** – SQLAlchemy ORM models.
- **enums.py / constant.py** – Domain-specific enums and constants.
---

# 🛠 Tech Stack

Backend

- FastAPI
- SQLAlchemy (Async ORM)
- PostgreSQL
- Alembic
- Pydantic

Authentication

- JWT
- bcrypt

Database

- PostgreSQL

Logging

- Python Logging

API Documentation

- Swagger UI
- ReDoc

---

# 📌 API Endpoints

## Authentication

| Method | Endpoint |
|---------|----------|
| POST | /users/register |
| POST | /users/login |
| POST | /users/refresh |
| GET | /users/profile |
| PATCH | /users/update |
| POST | /users/change-password |
| POST | /users/logout |

---

## Tasks

| Method | Endpoint |
|---------|----------|
| POST | /tasks/create |
| GET | /tasks/getAllTask |
| GET | /tasks/getTaskByID |
| PATCH | /tasks/updateTask |
| PATCH | /tasks/update_task_status |
| DELETE | /tasks/deleteTask |
| PATCH | /tasks/recoverTask |

---

## Admin

| Method | Endpoint |
|---------|----------|
| GET | /admin/users |
| GET | /admin/dashboard |
| DELETE | /admin/delete |
| PATCH | /admin/restore |
| PATCH | /admin/update-status |
| PATCH | /admin/update-role |

---

# 📊 Database Highlights

The application contains relational database design with:

- Users
- Tasks
- User Sessions

Features implemented:

- Foreign Keys
- Relationships
- Soft Delete
- Timestamp Tracking
- Session Tracking

---

# 📄 Logging

Important events are logged.

Examples:

- User Registration
- Login
- Logout
- Password Change
- Task Operations
- Authorization Events
- Database Errors

Sensitive information like passwords and tokens are never logged.

---

# 🚀 Production Practices

Implemented:

- Async Database Operations
- Dependency Injection
- Exception Handling
- Centralized Logging
- JWT Authentication
- Refresh Tokens
- Session Revocation
- Soft Delete
- Clean Service Layer
- Repository Pattern
- Role Based Authorization
- Secure Password Hashing

---

# 🔮 Planned Improvements

Future enhancements include:

- Forgot Password via Email
- Email Verification
- Login History
- Rate Limiting
- Redis Token Blacklisting
- Docker Support
- CI/CD Pipeline
- Unit Testing
- Integration Testing
- Background Session Cleanup
- API Versioning

---

# ▶ Running the Project

Clone the repository

```bash
git clone <repository-url>
```

Create virtual environment

```bash
python -m venv venv
```

Activate environment

Windows

```bash
venv\Scripts\activate
```

Linux

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run migrations

```bash
alembic upgrade head
```

Run application

```bash
uvicorn app.main:app --reload
```

Swagger

```
http://localhost:8000/docs
```

---

# 👨‍💻 About This Project

This project was built to practice designing production-ready backend systems rather than only implementing CRUD operations.

It demonstrates:

- Secure Authentication
- Authorization
- Session Management
- Clean Architecture
- Scalable Backend Design
- REST API Best Practices
- Database Design
- Production-Oriented Development

---

## 👤 Author

**Kabir Seth**

Backend Developer

FastAPI • Python • PostgreSQL • SQLAlchemy • JWT Authentication
