# Security Documentation

This document outlines the security measures and protocols implemented in the Cloud Drive API to protect user data and ensure system integrity.

## Authentication & Authorization

### JWT (JSON Web Tokens)
Authentication is handled via JWTs.

1.  **Access Token**: 
    *   Short-lived (default: 30 minutes).
    *   Used to authenticate API requests.
    *   Passed in the `Authorization: Bearer <token>` header.
    *   Contains user claims (ID, email, roles).

2.  **Refresh Token**:
    *   Long-lived (default: 7 days).
    *   Used to obtain new access tokens without re-login.
    *   **Storage**: Stored in a secure **HTTPOnly** cookie. This prevents XSS attacks from accessing the token via JavaScript.
    *   **Protection**: The refresh token itself is hashed before being stored in the database. A "pepper" is used during hashing for additional security.

### Password Security
*   **Hashing**: Passwords are never stored in plain text. We use robust hashing algorithms (Argon2 or Bcrypt via `passlib`).
*   **Validation**: Password strength can be enforced at the schema level.

## Data Protection

### File Storage Security
*   **Access Control**: Files are associated with an `owner_id`. The `FileService` verifies ownership before allowing download, rename, or deletion operations.
*   **Path Traversal Prevention**: Filenames are sanitized, and the system uses `uuid` for internal storage paths to prevent users from manipulating paths to access unauthorized system files.

## Network & API Security

### Rate Limiting
*   **Library**: `slowapi` (based on `limits`).
*   **Policy**: A global rate limit (e.g., "2000/minute") is applied to endpoints to prevent abuse and DoS attacks.
*   **Identification**: Rate limits are tracked by IP address.

### CORS (Cross-Origin Resource Sharing)
*   Configured to allow specific trusted origins (e.g., `http://localhost:5173` for the frontend).
*   Prevents malicious websites from making requests to the API on behalf of the user.

### Cookie Security
Cookies used for refresh tokens are configured with:
*   `HttpOnly=True`: Inaccessible to JavaScript.
*   `Secure=True`: Only sent over HTTPS (configurable for local dev).
*   `SameSite="Lax"`: Protects against CSRF attacks.

## Best Practices Checklist

- [x] **secrets management**: All sensitive keys (API keys, DB passwords, JWT secrets) are loaded from environment variables (`.env`).
- [x] **Input Validation**: usage of Pydantic models ensures that incoming data matches expected types and formats, preventing injection attacks.
- [x] **Output Sanitization**: API responses return structured JSON functionality, reducing XSS risks.
