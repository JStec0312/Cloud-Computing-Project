# Architecture Documentation

This project follows the **Clean Architecture** (also known as Hexagonal Architecture or Onion Architecture) principles. The primary goal is to separate concerns, making the system easier to test, maintain, and extend.

## High-Level Overview

The application is divided into concentric layers, where dependencies point inwards. The inner layers define the business rules and are independent of external frameworks or drivers.

```mermaid
graph TD
    API[API Layer<br>(routers, schemas)] --> App[Application Layer<br>(services, use cases)]
    App --> Domain[Domain Layer<br>(entities, enums)]
    Infra[Infrastructure Layer<br>(db, storage, security)] --> Domain
    Infra -- implements interfaces --> App
```

## Layers

### 1. Domain Layer (`src/domain`)
This is the core of the application. It contains the enterprise business rules and entities. It has **no dependencies** on other layers.

*   **Entities**: Pure Python classes representing business objects (e.g., `User`, `File`).
*   **Enums**: Value objects and enumerations.

### 2. Application Layer (`src/application`)
This layer contains application-specific business rules. It orchestrates the flow of data to and from the domain entities.

*   **Services**: `AuthService`, `FileService`, etc., contain the logic for specific features.
*   **Abstractions**: Defines interfaces (protocols) for repositories and external services (e.g., `IFileStorage`). This allows the application layer to rely on abstractions rather than concrete implementations.

### 3. API Layer (`src/api`)
This layer acts as the Interface Adapter. It handles HTTP requests, input validation, and formatting responses.

*   **Routers**: FastAPI routers defining endpoints (`/auth`, `/files`).
*   **Schemas**: Pydantic models for request/response validation (DTOs).
*   **Dependencies**: FastAPI dependency injection setup.

### 4. Infrastructure Layer (`src/infrastructure`)
This layer connects the application to external resources like databases, file systems, and third-party libraries.

*   **Database**: SQLAlchemy models and Alembic migrations.
*   **Repositories**: Concrete implementations of repository interfaces (e.g., loading data from Postgres).
*   **Storage**: Implementations for file storage (Local disk or AWS S3).
*   **Security**: Concrete implementations for password hashing and token management.
*   **Unit of Work (UoW)**: Manages database transactions.

## Key Design Patterns

### Unit of Work (UoW)
We use the Unit of Work pattern (`src/infrastructure/uow.py`) to handle database transactions atomically. The Service layer interacts with the UoW to commit or rollback changes, ensuring data integrity.

### Dependency Injection
FastAPI's dependency injection system (`src/deps.py`) is used to provide concrete implementations (like `SqlAlchemyUoW`) to the application services at runtime.

### Repository Pattern
Data access is abstracted via the Repository pattern. Services do not write raw SQL; they call methods like `get_by_id` or `add` on a repository object found within the UoW.
