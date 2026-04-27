"""FastAPI application entry point — v2 skeleton (post-P2).

P1 cleared v1. P2 adds the /api/v1 router structure: /health (public) and
/sessions (auth-protected, returns 501 until P3 wires the harness in).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, sessions
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.settings import settings, setup_logging

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

app.include_router(health.router, prefix=API_PREFIX)
app.include_router(sessions.router, prefix=API_PREFIX)
