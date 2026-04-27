"""FastAPI application entry point — v2 skeleton.

This is the post-v1 cleanup state. There are NO domain routers mounted here
yet; the only endpoint is /api/v1/health. P2 will add /api/sessions to wire
the harness in. Until then this app exists only to verify the surrounding
plumbing (CORS, middleware, auth) still loads cleanly.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_id import RequestIDMiddleware

setup_logging()

app = FastAPI(title=settings.app_name, version="0.2.0")

register_error_handlers(app)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"


@app.get(f"{API_PREFIX}/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
