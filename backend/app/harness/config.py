"""Harness config — Anthropic client factory.

Reads .env, picks the right transport (direct Anthropic API vs Azure-hosted
Anthropic proxy), and returns a wired client. No global state, no caching —
callers hold the returned `HarnessClient`.

Azure proxy detection: when LLM_PROVIDER=azure_openai *and* the base URL
contains "anthropic" (Azure AI Foundry's Anthropic deployment serves the
Messages protocol), point the Anthropic SDK at it with the Azure key.
Otherwise use the direct ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from anthropic import Anthropic
from dotenv import load_dotenv

Provider = Literal["anthropic", "azure"]


@dataclass(frozen=True)
class HarnessClient:
    """Resolved Anthropic SDK client + the model to call."""

    client: Anthropic
    default_model: str
    provider: Provider


class HarnessConfigError(RuntimeError):
    """Raised when env config is missing or inconsistent."""


def load_env(path: Path | str | None = None) -> None:
    """Load a .env file if present. Safe to call repeatedly.

    If `path` is None, walks up from cwd to find .env (dotenv default).
    """
    load_dotenv(path) if path is not None else load_dotenv()


def _is_azure_anthropic(provider: str, base_url: str) -> bool:
    return provider.lower() == "azure_openai" and "anthropic" in base_url.lower()


def build_client(*, env: dict[str, str] | None = None) -> HarnessClient:
    """Build a HarnessClient from environment variables.

    Args:
        env: Override the env source (defaults to os.environ). For tests.

    Resolution order:
        1. LLM_PROVIDER=azure_openai + AZURE_OPENAI_BASE_URL contains "anthropic"
           → Azure proxy. Use AZURE_OPENAI_API_KEY + AZURE_OPENAI_BASE_URL.
           Model from AZURE_OPENAI_DEFAULT_MODEL.
        2. Otherwise → direct Anthropic. Use ANTHROPIC_API_KEY.
           Model from ANTHROPIC_DEFAULT_MODEL.

    Raises:
        HarnessConfigError if required keys are missing.
    """
    e = env if env is not None else os.environ

    provider = (e.get("LLM_PROVIDER") or "anthropic").strip()
    azure_base = (e.get("AZURE_OPENAI_BASE_URL") or "").strip()

    if _is_azure_anthropic(provider, azure_base):
        api_key = (e.get("AZURE_OPENAI_API_KEY") or "").strip()
        model = (e.get("AZURE_OPENAI_DEFAULT_MODEL") or "").strip()
        if not api_key:
            raise HarnessConfigError("AZURE_OPENAI_API_KEY is empty")
        if not model:
            raise HarnessConfigError("AZURE_OPENAI_DEFAULT_MODEL is empty")
        client = Anthropic(api_key=api_key, base_url=azure_base)
        return HarnessClient(client=client, default_model=model, provider="azure")

    api_key = (e.get("ANTHROPIC_API_KEY") or "").strip()
    model = (e.get("ANTHROPIC_DEFAULT_MODEL") or "").strip()
    if not api_key:
        raise HarnessConfigError(
            "ANTHROPIC_API_KEY is empty (and Azure proxy is not configured)"
        )
    if not model:
        raise HarnessConfigError("ANTHROPIC_DEFAULT_MODEL is empty")
    client = Anthropic(api_key=api_key)
    return HarnessClient(client=client, default_model=model, provider="anthropic")
