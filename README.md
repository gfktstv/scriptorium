# Scriptorium
## Local Development Setup

### Prerequisites

*   **Python 3.10+**
*   **postresql**
*   **Docker** and **Docker Compose**

### 1. Clone the repository

```bash
git clone https://github.com/gfktstv/scriptorium.git
cd scriptorium
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

You can install the dependencies using the provided `pyproject.toml`.

```bash
pip install -e .
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory. You can use the example file as a template:

```bash
cp .env.example .env
```

### 5. Start the Database

Start the PostgreSQL database using Docker Compose. This will create the volume and user based on your `.env` variables.

```bash
docker compose up -d
```

### 6. Run the Application

You can start the development server using Uvicorn. Run this command from the **root** of the project:

```bash
python3 -m app.main
```

The API will be available at:
*   **API Root:** `http://127.0.0.1:8000`
*   **Interactive Docs (Swagger):** `http://127.0.0.1:8000/docs`

## Directory Structure

```text
app/
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── security.py
├── db/
│   ├── __init__.py
│   ├── base.py
│   └── session.py
├── models/
│   ├── __init__.py
│   └── user.py
├── routers/
│   ├── __init__.py
│   └── users.py
├── schemas/
│   ├── __init__.py
│   └── user.py
├── __init__.py
└── main.py
```

---

## Project Documentation

### **app/**
The main application directory.

*   **main.py**
    The entry point of the application. This file initializes the FastAPI app and connects the routers.

### **app/core/**
This directory contains the central logic and settings that are used across the entire application. It does not contain business logic.
*   **config.py**: Handles application settings and environment variables (using pydantic-settings).
*   **security.py**: Contains security tools, such as password hashing and token validation.
*   **exceptions.py**: (Optional) Defines custom error handlers.
*   **logging.py**: (Optional) Configures how the application records logs.

### **app/db/**
This directory handles the technical connection to the database.
*   **session.py**: Creates the database engine and establishes the connection session.
*   **base.py**: Defines the Base class for ORM models. This is required for SQLAlchemy and migrations.

### **app/models/**
This directory contains the database table definitions (SQLAlchemy models).
*   **Naming convention**: Use singular names for files (e.g., `user.py`), as each file defines a single entity type.

### **app/schemas/**
This directory contains Pydantic models used for data validation. These determine what data the API accepts and what it returns.
*   **Naming convention**: Use singular names for files (e.g., `user.py`).

### **app/routers/**
This directory contains the API endpoints (routes). It links the business logic, schemas, and models together.
*   **Naming convention**: Use plural names for files (e.g., `users.py`), as each file manages a collection of resources.