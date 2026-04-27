"""Core app config — slim Pydantic Settings.

Loads from project-root .env. LLM provider settings live in
`app.harness.config` (the v2 harness owns its own client wiring) — this file
only carries app-level concerns: CORS, auth (JWT), and Supabase identity.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

# backend/app/core/config.py → project root is 4 levels up
_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


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
