"""Application configuration loaded from environment variables.

Reads from the **project root** .env (one level above backend/), so there is
only one .env file to maintain for the entire mono-repo.

Priority: real environment variable > root .env > default value here.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

# backend/app/core/config.py → project root is 4 levels up
_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GEMINI = "gemini"
    QWEN = "qwen"


class Settings(BaseSettings):
    # --- API ---
    app_name: str = "Design Copilot Backend"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080", "http://localhost:8081"]

    # --- Supabase ---
    # 前端用 VITE_ prefix（Vite 規定），後端也讀同一份，不重複宣告
    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_URL", "VITE_SUPABASE_URL"),
    )
    supabase_service_key: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_SERVICE_KEY", "VITE_SUPABASE_SERVICE_ROLE_KEY"),
    )
    supabase_access_token: str = ""  # Supabase Management API token (optional)
    jwt_secret: str = ""  # Supabase JWT secret (Settings > API > JWT Secret)

    # --- LLM Provider ---
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC

    # --- Anthropic ---
    anthropic_api_key: str = ""
    anthropic_default_model: str = Field(
        default="claude-sonnet-4-6",
        validation_alias=AliasChoices("ANTHROPIC_DEFAULT_MODEL", "DEFAULT_MODEL"),
    )
    anthropic_fast_model: str = Field(
        default="claude-haiku-4-5",
        validation_alias=AliasChoices("ANTHROPIC_FAST_MODEL", "FAST_MODEL"),
    )
    anthropic_max_output_tokens: int = Field(
        default=16384,
        description="Anthropic API requires max_tokens. Set to model's max output capacity.",
    )

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o"
    openai_fast_model: str = "gpt-4o-mini"

    # --- Azure OpenAI ---
    # 使用 OpenAI-compatible endpoint（/openai/v1/）
    azure_openai_api_key: str = ""
    azure_openai_base_url: str = ""  # e.g. https://<resource>.cognitiveservices.azure.com/openai/v1/
    azure_openai_default_model: str = ""  # deployment name or model name
    azure_openai_fast_model: str = ""

    # --- Google Gemini ---
    # OpenAI-compatible endpoint: https://generativelanguage.googleapis.com/v1beta/openai/
    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_default_model: str = "gemini-2.5-flash"
    gemini_fast_model: str = "gemini-2.0-flash-lite"

    # --- Alibaba Qwen (通義千問) ---
    # DashScope OpenAI-compatible endpoint
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_default_model: str = "qwen-plus"
    qwen_fast_model: str = "qwen-turbo"

    # --- Convenience accessors (resolved by provider) ---
    _MODEL_MAP = {
        LLMProvider.ANTHROPIC: ("anthropic_default_model", "anthropic_fast_model", "anthropic_api_key"),
        LLMProvider.OPENAI: ("openai_default_model", "openai_fast_model", "openai_api_key"),
        LLMProvider.AZURE_OPENAI: ("azure_openai_default_model", "azure_openai_fast_model", "azure_openai_api_key"),
        LLMProvider.GEMINI: ("gemini_default_model", "gemini_fast_model", "gemini_api_key"),
        LLMProvider.QWEN: ("qwen_default_model", "qwen_fast_model", "qwen_api_key"),
    }

    @property
    def default_model(self) -> str:
        attr = self._MODEL_MAP[self.llm_provider][0]
        return getattr(self, attr)

    @property
    def fast_model(self) -> str:
        attr = self._MODEL_MAP[self.llm_provider][1]
        return getattr(self, attr)

    @property
    def active_api_key(self) -> str:
        attr = self._MODEL_MAP[self.llm_provider][2]
        return getattr(self, attr)

    # --- Web Search (optional — enables evidence grounding) ---
    web_search_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("WEB_SEARCH_ENABLED"),
        description="Enable web search tool for LLM calls. Requires provider support.",
    )
    tavily_api_key: str = ""

    # --- TRIZ Knowledge Base ---
    triz_kb_path: str = "../rd_assistant_design_system/triz_knowledge_base"

    model_config = {
        "env_file": str(_ROOT_ENV),
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # 跳過 VITE_* 等前端專用變數
    }


settings = Settings()
