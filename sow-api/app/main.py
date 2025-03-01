import os

import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from keycloak import KeycloakOpenID
from jose import jwt, jwk
from jose.utils import base64url_decode
from jose.exceptions import JWTError, JWSError
from .models import WaffleReview

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI()

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET")

keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
    client_secret_key=KEYCLOAK_CLIENT_SECRET,
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

auth_scheme = HTTPBearer()


def decode_token(token: str) -> dict:
    try:
        # 1. Get the well-known configuration (contains JWKS URI)
        well_known = keycloak_openid.well_known()

        # 2. Fetch the JWKS (JSON Web Key Set)
        jwks_uri = well_known.get("jwks_uri")
        if not jwks_uri:
            raise HTTPException(status_code=500, detail="JWKS URI not found in well-known config.")
        jwks = keycloak_openid.connection.raw_get(jwks_uri).json()

        # 3. Get the Key ID (kid) from the JWT header (without verifying the signature)
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        if not kid:
            raise HTTPException(status_code=401, detail="No 'kid' found in JWT header")

        # 4. Find the matching key in the JWKS
        key_found = False
        for key in jwks['keys']:
            if key['kid'] == kid:
                public_key = jwk.construct(key)
                key_found = True
                break  # Exit the loop once the key is found

        if not key_found:
            raise HTTPException(status_code=401, detail=f"No matching key found for kid: {kid}")

        # 5.  Get the key material
        message, encoded_sig = token.rsplit(sep='.', maxsplit=1)
        message_bytes = message.encode('utf-8')
        encoded_sig_bytes = encoded_sig.encode('utf-8')
        sig = base64url_decode(encoded_sig_bytes)
        key = public_key.to_pem()

        # 6. Decode and Verify the JWT
        decoded_token = jwt.decode(
            token,
            key,
            algorithms=["RS256"],  # Keycloak's default signing algorithm
            audience=KEYCLOAK_CLIENT_ID,
            options={"verify_exp": True}  # Verify expiration
        )
        return decoded_token

    except JWTError as e:
        log.error(f"JWTError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWSError as e:
        log.error(f"JWSError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid key: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def get_current_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        return decoded_token
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.post("/api/waffle/reviews")
async def create_review(review: WaffleReview, user: dict = Depends(get_current_user)):
    # You now have the authenticated user information in `user`
    log.info(f"Received review from user: {user['preferred_username']}")
    log.info(f"Review: {review.model_dump()}")
    return {"message": "Review submitted successfully!", "user": user['preferred_username']} #return user info

# Added this get endpoint, so Keycloak has a userinfo endpoint.
@app.get("/userinfo")
async def get_userinfo(user: dict = Depends(get_current_user)):
  return user
