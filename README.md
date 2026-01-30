# Stunning Octo Waffle (SOW)

This project demonstrates a complete authentication flow using OpenID Connect (OIDC) with Keycloak as the Identity Provider (IdP), a FastAPI backend, and a React frontend.

![sow-app-logged-in.jpg](docs/sow-app-logged-in.jpg)

## Architecture

The project consists of three main components:
1.  **sow-app (Frontend)**: A React application that handles user interaction and authentication using OIDC. It retrieves tokens from Keycloak and sends them to the backend API.
2.  **sow-api (Backend)**: A FastAPI application that validates the JWT tokens received from the frontend against Keycloak's public keys.
3.  **Keycloak (IdP)**: The authentication server that manages users and issues tokens.

## Prerequisites

- **Docker**: For running the entire stack easily.
- **Node.js** (v18+) & **npm**: If running the frontend locally.
- **Python** (v3.12+): If running the backend locally.

## Running with Docker (Recommended)

To start all services (Keycloak, API, Frontend):

```bash
docker-compose up --build
```

### Accessing the Services

1.  **Keycloak**: [http://localhost:8080](http://localhost:8080)
    -   Admin Console: Login with `admin` / `admin_password`.
2.  **Frontend App**: [http://localhost:3000](http://localhost:3000)
    -   Login with the test user: `testuser` / `testpassword`.
3.  **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)

## About OIDC (OpenID Connect)

This project uses OIDC, an identity layer on top of the OAuth 2.0 protocol.

1.  **Login**: The user clicks "Login" in the frontend. They are redirected to Keycloak.
2.  **Authentication**: The user enters credentials in Keycloak.
3.  **Token Issuance**: Keycloak redirects back to the frontend with an authorization code, which is exchanged for an ID Token (who the user is) and an Access Token (authorization to access resources).
4.  **API Request**: The frontend includes the Access Token in the `Authorization` header (`Bearer <token>`) when making requests to the backend.
5.  **Validation**: The backend verifies the token's signature using Keycloak's public keys (retrieved via the `.well-known` endpoint) to ensure it's valid and trusted.

## Keycloak Configuration

-   **Realm**: `sow`
-   **Client ID**: `sow-app-client` (Frontend), `sow-api-client` (Backend Audience)
-   **Well-known Endpoint**: [http://localhost:8080/realms/sow/.well-known/openid-configuration](http://localhost:8080/realms/sow/.well-known/openid-configuration)
