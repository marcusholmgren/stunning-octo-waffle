import os
import logging
import time
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, jwk
from jose.exceptions import JWTError, JWSError

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
log = logging.getLogger(__name__)

# --- Configuration ---
IDP_URL = os.environ.get("IDP_URL")
IDP_AUDIENCE = os.environ.get("IDP_AUDIENCE", "your-default-audience")

if not IDP_URL:
    log.error("IDP_URL environment variable must be set.")
    raise RuntimeError("Missing IDP_URL configuration.")

WELL_KNOWN_URL = f"{IDP_URL.rstrip('/')}/.well-known/openid-configuration"
ALLOWED_ALGORITHMS = ["RS256"]

# --- Caching for Well-Known Config and JWKS ---
CACHE_TTL_SECONDS = 300
_well_known_config_cache = {"data": None, "timestamp": 0.0}
_jwks_cache = {"data": None, "timestamp": 0.0, "jwks_uri": None}
_public_key_cache = {} # Simple dict cache for public keys {kid: (key_pem, timestamp)}

# --- Async HTTP Client ---
# Use a single client instance for connection pooling
http_client = httpx.AsyncClient(timeout=10)

async def close_auth_client():
    await http_client.aclose()
    log.info("HTTPX client closed.")

async def get_well_known_config():
    """Fetches the OIDC well-known configuration asynchronously, with caching."""
    now = time.time()
    if now - _well_known_config_cache["timestamp"] < CACHE_TTL_SECONDS and _well_known_config_cache["data"]:
        return _well_known_config_cache["data"]

    try:
        response = await http_client.get(WELL_KNOWN_URL)
        response.raise_for_status()
        config = response.json()
        _well_known_config_cache["data"] = config
        _well_known_config_cache["timestamp"] = now
        log.info("Fetched and cached well-known configuration.")
        return config
    except httpx.RequestError as e:
        log.error(f"Failed to fetch well-known configuration via httpx: {e}")
        if _well_known_config_cache["data"]:
            log.warning("Returning stale well-known configuration due to fetch error.")
            return _well_known_config_cache["data"]
        raise HTTPException(status_code=503, detail="Could not retrieve OIDC configuration.")
    except Exception as e: # Catch potential JSON decode errors or other issues
        log.error(f"Error processing well-known configuration response: {e}")
        raise HTTPException(status_code=500, detail="Error processing OIDC configuration response.")


async def get_jwks():
    """Fetches the JWKS asynchronously using the URI from the well-known config, with caching."""
    well_known = await get_well_known_config() # Await the async call
    jwks_uri = well_known.get("jwks_uri")
    if not jwks_uri:
        log.error("JWKS URI not found in well-known config.")
        raise HTTPException(status_code=500, detail="JWKS URI not configured.")

    now = time.time()
    if (now - _jwks_cache["timestamp"] < CACHE_TTL_SECONDS and
            _jwks_cache["data"] and
            _jwks_cache["jwks_uri"] == jwks_uri):
        return _jwks_cache["data"]

    try:
        response = await http_client.get(jwks_uri)
        response.raise_for_status()
        jwks = response.json()
        _jwks_cache["data"] = jwks
        _jwks_cache["timestamp"] = now
        _jwks_cache["jwks_uri"] = jwks_uri
        log.info("Fetched and cached JWKS.")
        # Clear the public key cache when JWKS is refreshed
        _public_key_cache.clear()
        log.info("Public key cache cleared due to JWKS refresh.")
        return jwks
    except httpx.RequestError as e:
        log.error(f"Failed to fetch JWKS via httpx: {e}")
        if _jwks_cache["data"] and _jwks_cache["jwks_uri"] == jwks_uri:
             log.warning("Returning stale JWKS due to fetch error.")
             return _jwks_cache["data"]
        raise HTTPException(status_code=503, detail="Could not retrieve JWKS.")
    except Exception as e: # Catch potential JSON decode errors or other issues
        log.error(f"Error processing JWKS response: {e}")
        raise HTTPException(status_code=500, detail="Error processing JWKS response.")


async def get_public_key(kid: str):
    """Finds the appropriate public key asynchronously, with caching."""
    now = time.time()
    # Check cache first
    cached_key = _public_key_cache.get(kid)
    if cached_key and now - cached_key[1] < CACHE_TTL_SECONDS:
        return cached_key[0] # Return cached PEM

    jwks = await get_jwks() # Await the async call
    if not jwks or 'keys' not in jwks:
         log.error("Invalid JWKS structure received.")
         raise HTTPException(status_code=500, detail="Invalid JWKS received from provider.")

    key_found = False
    for key_dict in jwks['keys']:
        if key_dict.get('kid') == kid:
            # Optional checks (already present in previous version)
            if 'use' in key_dict and key_dict.get('use') != 'sig':
                continue
            if 'alg' in key_dict and key_dict.get('alg') not in ALLOWED_ALGORITHMS:
                 continue

            try:
                public_key = jwk.construct(key_dict)
                public_key_pem = public_key.to_pem().decode('utf-8')
                # Cache the constructed key
                _public_key_cache[kid] = (public_key_pem, now)
                log.debug(f"Constructed and cached public key for kid: {kid}")
                key_found = True
                return public_key_pem
            except JWSError as e:
                log.error(f"Failed to construct public key for kid {kid}: {e}")
                raise HTTPException(status_code=500, detail=f"Could not construct public key for kid: {kid}")

    if not key_found:
        log.warning(f"No matching public key found for kid: {kid} in current JWKS.")
        raise HTTPException(status_code=401, detail=f"Public key for token signature not found (kid: {kid})")


async def decode_token(token: str) -> dict:
    """Decodes and verifies the JWT token asynchronously using OIDC discovery and JWKS."""
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        alg = unverified_header.get('alg')

        if not kid:
            log.error("No 'kid' found in JWT header")
            raise HTTPException(status_code=401, detail="Token header missing 'kid'")
        if not alg:
            log.error("No 'alg' found in JWT header")
            raise HTTPException(status_code=401, detail="Token header missing 'alg'")

        if alg not in ALLOWED_ALGORITHMS:
             log.error(f"Token algorithm '{alg}' not in allowed list: {ALLOWED_ALGORITHMS}")
             raise HTTPException(status_code=401, detail=f"Invalid token algorithm: {alg}")

        # Await the async public key retrieval
        public_key_pem = await get_public_key(kid)

        options = {
            "verify_signature": True, "verify_aud": True, "verify_iat": True,
            "verify_exp": True, "verify_nbf": True, "verify_iss": True,
            "require_aud": False, "require_iat": True, "require_exp": True,
            "require_iss": True,
        }

        decoded_token = jwt.decode(
            token,
            public_key_pem,
            algorithms=[alg],
            audience=IDP_AUDIENCE,
            options=options
        )
        log.info(f"Token successfully decoded for user: {decoded_token.get('preferred_username', 'N/A')}")
        return decoded_token

    except JWTError as e:
        log.error(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
        )
    except JWSError as e:
        log.error(f"JWSError during token processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing token key.",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        log.exception(f"Unexpected error during token decoding: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token processing.",
        )

auth_scheme = HTTPBearer()

# get_current_user is already async, so it can call decode_token directly
async def get_current_user(token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    return await decode_token(token.credentials) # Await the async decode
