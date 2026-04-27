"""App-level settings + structured logging.

Merged from the previous app/core/{config,logging}.py — two ~45-line files
for one Pydantic Settings class and one JSON log formatter didn't earn the
extra package layer. LLM provider settings stay in app.harness.config (the
v2 harness owns its own client wiring); this file carries only app-level
concerns: CORS, auth (JWT), Supabase identity, and the JSON log format.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

from app.middleware.request_id import get_request_id

# backend/app/settings.py → project root is 3 levels up (project/.env)
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


# ────────────────────────────────────────────────────────────────────────────
# Settings — read from project-root .env via Pydantic Settings
# ────────────────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    # --- API ---
    app_name: str = "Design Copilot Backend"
    debug: bool = False
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8081",
    ]

    # --- Supabase (identity / auth only — no DB layer in v2 harness) ---
    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_URL", "VITE_SUPABASE_URL"),
    )
    supabase_service_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SUPABASE_SERVICE_KEY", "VITE_SUPABASE_SERVICE_ROLE_KEY"
        ),
    )
    supabase_access_token: str = ""  # Supabase Management API token (optional)
    jwt_secret: str = ""  # Supabase JWT secret (Settings > API > JWT Secret)

    model_config = {
        "env_file": str(_ROOT_ENV),
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # skip VITE_*, ANTHROPIC_*, AZURE_*, etc. — owned elsewhere
    }


settings = Settings()


# ────────────────────────────────────────────────────────────────────────────
# Structured logging — single-line JSON with request_id correlation
# ────────────────────────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> None:
    """Configure root logger with structured JSON output."""
    log_level = logging.DEBUG if os.getenv("ENV", "dev") == "dev" else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(log_level)
    # Avoid duplicate handlers if called multiple times
    root.handlers.clear()
    root.addHandler(handler)
