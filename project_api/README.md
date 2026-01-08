# Cloud Drive API

A robust REST API for a cloud storage service, built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. This application allows users to upload, download, manage files and folders, and includes features like file versioning and rate limiting.

## 🚀 Features

*   **Authentication & Authorization**:
    *   Secure User Registration and Login.
    *   JWT-based Access Tokens.
    *   Refresh Tokens stored in secure HTTP-only cookies.
    *   Password hashing using Argon2/Bcrypt.
*   **File Management**:
    *   Upload and Download files.
    *   Create and manage nested Folders.
    *   Rename and Delete files/folders.
    *   **File Versioning**: Access previous versions of files.
    *   Directory Listing.
*   **Storage Providers**:
    *   **Local Storage**: Store files on the server's filesystem.
    *   **AWS S3**: Store files in an S3 bucket (configurable).
*   **Security & Performance**:
    *   Rate Limiting (Token Bucket algorithm via `slowapi`).
    *   Input validation with Pydantic.
    *   CORS configuration.

## 🛠️ Tech Stack

*   **Language**: Python 3.10+
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
*   **Database**: PostgreSQL
*   **ORM**: SQLAlchemy (Async)
*   **Migrations**: Alembic
*   **Containerization**: Docker & Docker Compose
*   **Testing**: Pytest & Pytest-Asyncio

## 📂 Project Structure

The project follows a Clean Architecture / Hexagonal Architecture pattern:

```
src/
├── api/            # Interface Adapters (Routers, Controllers, Schemas)
├── application/    # Application Business Rules (Services, Use Cases)
├── domain/         # Enterprise Business Rules (Entities, Enums)
├── infrastructure/ # Frameworks & Drivers (Database, Storage impl, Repositories)
├── config/         # Configuration settings
└── common/         # Shared utilities
```

## ⚙️ Configuration

The application is configured using environment variables. You can verify the required variables in `.env.example`.

### Key Environment Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DB_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db` |
| `JWT_SECRET` | Secret key for signing tokens | `your_secret` |
| `STORAGE_TYPE` | Storage backend to use | `local` or `s3` |
| `LOCAL_STORAGE_PATH`| Path for files when using local storage| `./local_storage_data` |
| `AWS_...` | AWS Credentials (if using S3) | - |

## 🚀 Getting Started

### Prerequisites

*   **Docker** and **Docker Compose**
*   *Or for local dev:* Python 3.10+ and PostgreSQL

### Option 1: Run with Docker (Recommended)

1.  **Clone the repository**.
2.  **Create `.env` file**:
    ```bash
    cp .env.example .env
    ```
    *Modify `.env` to set your preferences (Database credentials will be handled by docker-compose for the db service, but ensure the app config matches).*

3.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
    The API will be available at `http://localhost:8000`.

### Option 2: Local Development

1.  **Set up virtual environment**:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    Create a `.env` file based on `.env.example` and ensure your local PostgreSQL database is running and accessible.

4.  **Run Migrations**:
    Apply database schema changes using Alembic.
    ```bash
    alembic upgrade head
    ```

5.  **Run the Server**:
    ```bash
    uvicorn src.main:app --reload
    ```

## 📚 API Documentation

Once the server is running, you can access the interactive API documentation:

*   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📖 Further Documentation

*   [**Architecture Guide**](docs/ARCHITECTURE.md): Detailed explanation of the Clean Architecture layers and design patterns.
*   [**Security Guide**](docs/SECURITY.md): Overview of authentication, authorization, and security protocols.

## 🧪 Running Tests

The project uses `pytest` for testing.

```bash
# Run all tests
pytest

# Run tests with output
pytest -v
```

## 🗄️ Database Migrations

*   **Create a new migration**:
    ```bash
    alembic revision --autogenerate -m "description of change"
    ```
*   **Apply migrations**:
    ```bash
    alembic upgrade head
    ```
