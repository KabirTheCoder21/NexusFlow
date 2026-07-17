# 🚀 Production-Ready Task Management API

A production-ready **Task Management REST API** built with **FastAPI**, **SQLAlchemy (Async)**, **PostgreSQL**, **JWT Authentication**, **Redis**, and **Docker**, following clean architecture and backend best practices.

> Designed to demonstrate secure authentication, scalable API design, session management, and production-ready backend development.

---

## 🔐 Authentication & Session Flow

**Highlights**

- JWT Access & Refresh Tokens
- Refresh Token Rotation
- Session-based Authentication
- Secure Logout with Session Revocation
- Multi-device Session Support (Max 5 Active Sessions)
- Refresh Token Hashing (Anti-Replay Protection)
- Automatic Session Validation on Every Request

---

## ✨ Features

### Authentication
- User Registration & Login
- JWT Authentication
- Refresh Token Rotation
- Logout
- Change Password
- Profile Management

### Task Management
- Create, Update & Delete Tasks
- Task Status Management
- Soft Delete & Restore

### Admin
- Dashboard Statistics
- User Management
- Role-Based Access Control (RBAC)

---

## 🛡️ Security

- bcrypt Password Hashing
- JWT Access & Refresh Tokens
- Refresh Token Rotation
- Session Revocation
- Role-Based Authorization
- Soft Delete
- Secure Logging
- Password Change Invalidates Active Sessions

---

## 🏗️ Tech Stack

- **FastAPI**
- **SQLAlchemy (Async)**
- **PostgreSQL (Neon)**
- **Redis (Upstash)**
- **Alembic**
- **Docker & Docker Compose**
- **JWT Authentication**
- **Pydantic**

---

## 📂 Project Structure

```text
src/
├── auth/
├── user/
├── tasks/
├── admin/
└── utils/

main.py
```

Feature-based modular architecture with Controllers, DTOs, Models, and Routers for better scalability and maintainability.

---

## 📌 Core API

### Authentication
- Register
- Login
- Refresh Token
- Profile
- Change Password
- Logout

### Tasks
- CRUD Operations
- Status Update
- Soft Delete & Restore

### Admin
- User Management
- Dashboard
- Role & Status Management

---

## 🚀 Production Practices

- Async Database Operations
- Clean Architecture
- Repository Pattern
- Dependency Injection
- Centralized Exception Handling
- Structured Logging
- Database Migrations (Alembic)
- Dockerized Deployment

---

## 👨‍💻 Author

**Kabir Seth**

Backend Developer | Python • FastAPI • PostgreSQL • SQLAlchemy
