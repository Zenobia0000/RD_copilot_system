"""Unit tests for harness config / client factory."""

from __future__ import annotations

import pytest

from app.harness.config import HarnessConfigError, build_client


# ────────────────────────────────────────────────────────────────────────────
# Azure-Anthropic proxy path
# ────────────────────────────────────────────────────────────────────────────

class TestAzureAnthropicProxy:
    def test_routes_to_azure_when_provider_and_url_match(self):
        env = {
            "LLM_PROVIDER": "azure_openai",
            "AZURE_OPENAI_BASE_URL": "https://x.services.ai.azure.com/anthropic/",
            "AZURE_OPENAI_API_KEY": "azure-key-xxx",
            "AZURE_OPENAI_DEFAULT_MODEL": "claude-sonnet-4-6",
        }
        result = build_client(env=env)

        assert result.provider == "azure"
        assert result.default_model == "claude-sonnet-4-6"
        # Anthropic SDK exposes base_url after init
        assert "anthropic" in str(result.client.base_url).lower()

    def test_provider_match_but_url_lacks_anthropic_falls_back(self):
        """If azure URL doesn't contain 'anthropic', it's a regular Azure
        OpenAI endpoint — not our path. Fall back to direct Anthropic."""
        env = {
            "LLM_PROVIDER": "azure_openai",
            "AZURE_OPENAI_BASE_URL": "https://x.openai.azure.com/openai/",
            "AZURE_OPENAI_API_KEY": "azure-key",
            "AZURE_OPENAI_DEFAULT_MODEL": "gpt-4o",
            "ANTHROPIC_API_KEY": "fallback-key",
            "ANTHROPIC_DEFAULT_MODEL": "claude-sonnet-4-6",
        }
        result = build_client(env=env)
        assert result.provider == "anthropic"
        assert result.default_model == "claude-sonnet-4-6"

    def test_azure_missing_api_key_raises(self):
        env = {
            "LLM_PROVIDER": "azure_openai",
            "AZURE_OPENAI_BASE_URL": "https://x.azure.com/anthropic/",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_DEFAULT_MODEL": "claude-sonnet-4-6",
        }
        with pytest.raises(HarnessConfigError, match="AZURE_OPENAI_API_KEY"):
            build_client(env=env)

    def test_azure_missing_model_raises(self):
        env = {
            "LLM_PROVIDER": "azure_openai",
            "AZURE_OPENAI_BASE_URL": "https://x.azure.com/anthropic/",
            "AZURE_OPENAI_API_KEY": "azure-key",
            "AZURE_OPENAI_DEFAULT_MODEL": "",
        }
        with pytest.raises(HarnessConfigError, match="AZURE_OPENAI_DEFAULT_MODEL"):
            build_client(env=env)


# ────────────────────────────────────────────────────────────────────────────
# Direct Anthropic path
# ────────────────────────────────────────────────────────────────────────────

class TestDirectAnthropic:
    def test_default_provider_uses_anthropic(self):
        env = {
            "ANTHROPIC_API_KEY": "sk-ant-xxx",
            "ANTHROPIC_DEFAULT_MODEL": "claude-opus-4-7",
        }
        result = build_client(env=env)
        assert result.provider == "anthropic"
        assert result.default_model == "claude-opus-4-7"

    def test_explicit_anthropic_provider(self):
        env = {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-ant-xxx",
            "ANTHROPIC_DEFAULT_MODEL": "claude-sonnet-4-6",
        }
        result = build_client(env=env)
        assert result.provider == "anthropic"

    def test_missing_api_key_raises(self):
        env = {"ANTHROPIC_DEFAULT_MODEL": "claude-sonnet-4-6"}
        with pytest.raises(HarnessConfigError, match="ANTHROPIC_API_KEY"):
            build_client(env=env)

    def test_missing_model_raises(self):
        env = {"ANTHROPIC_API_KEY": "sk-ant-xxx"}
        with pytest.raises(HarnessConfigError, match="ANTHROPIC_DEFAULT_MODEL"):
            build_client(env=env)

    def test_whitespace_in_keys_is_stripped(self):
        env = {
            "ANTHROPIC_API_KEY": "  sk-ant-xxx  ",
            "ANTHROPIC_DEFAULT_MODEL": "  claude-opus-4-7  ",
        }
        result = build_client(env=env)
        assert result.default_model == "claude-opus-4-7"
