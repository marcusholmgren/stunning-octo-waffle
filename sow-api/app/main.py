import os
import logging
import httpx
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from .models import WaffleReview
from .auth import get_current_user, set_http_client

logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
log = logging.getLogger(__name__)

# --- Async HTTP Client Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create and initialize the HTTP client
    client = httpx.AsyncClient(timeout=10)
    set_http_client(client)
    log.info("HTTP client created and initialized.")

    yield

    # Shutdown: Close the HTTP client gracefully
    await client.aclose()
    log.info("HTTP client closed.")

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# --- FastAPI Setup ---
origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins], # Strip whitespace from origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.post("/api/waffle/reviews")
async def create_review(review: WaffleReview, user: dict = Depends(get_current_user)):
    log.info(f"Received review from user: {user.get('preferred_username', 'N/A')}")
    log.info(f"Review: {review.model_dump()}")
    return {"message": "Review submitted successfully!", "user": user.get('preferred_username')}

@app.get("/userinfo")
async def get_userinfo(user: dict = Depends(get_current_user)):
  return user
