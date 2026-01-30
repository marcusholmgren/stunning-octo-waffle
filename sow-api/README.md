# Stunning Octo Waffle API

FastAPI backend for the SOW application.

## Getting Started

The recommended way to run the application is using Docker Compose from the root of the repository.

### Running Locally

To run the API locally, you need Python installed (refer to `pyproject.toml` or `.python-version` for version).

1.  Install dependencies:
    ```bash
    pip install "fastapi[standard]" "python-jose[cryptography]" httpx
    ```
    Or if you are using a package manager that supports `pyproject.toml` (like `uv` or `poetry`), use that.

2.  Set Environment Variables:
    You need to set the following environment variables:

    | Variable | Description | Example |
    | :--- | :--- | :--- |
    | `IDP_URL` | The URL of the Identity Provider (Keycloak) | `http://localhost:8080/realms/sow` |
    | `IDP_AUDIENCE` | The expected audience in the JWT token (optional) | `account` |
    | `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000,http://localhost:5173` |

3.  Run the application:
    ```bash
    export IDP_URL=http://localhost:8080/realms/sow
    uvicorn app.main:app --reload
    ```
    (Adjust `IDP_URL` if your Keycloak is running elsewhere).

### Tests
To run the tests, use the following command:

```bash
# Set a dummy IDP_URL for tests
export IDP_URL=http://mock-idp
pytest
```
