"""Tests for settings and provider router imports."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import Settings  # noqa: E402
from app.services import llm_provider_router  # noqa: E402
from app.services.autonomous_role_agents import (  # noqa: E402
    ROLE_DEFINITIONS,
    _provider_config_for_role,
)
from app.services.llm_provider_router import (  # noqa: E402
    AIMLAPI_DEFAULT_BASE_URL,
    get_provider_config,
    resolve_aimlapi_base_url,
)


class ProviderRouterTests(unittest.TestCase):
    def test_declared_providers_load_without_credentials(self) -> None:
        expected = {
            "openai": None,
            "anthropic": None,
            "featherless": "https://api.featherless.ai/v1",
            "aimlapi": "https://api.aimlapi.com/v1",
        }
        default_settings = Settings(
            featherless_base_url="https://api.featherless.ai/v1",
            aiml_base_url=AIMLAPI_DEFAULT_BASE_URL,
            aimlapi_base_url=AIMLAPI_DEFAULT_BASE_URL,
        )

        with patch.object(llm_provider_router, "settings", default_settings):
            for provider, base_url in expected.items():
                config = get_provider_config(provider)
                self.assertEqual(config.name, provider)
                self.assertEqual(config.base_url, base_url)

    def test_legacy_aimlapi_base_url_overrides_new_default(self) -> None:
        settings = Settings(
            aiml_base_url=AIMLAPI_DEFAULT_BASE_URL,
            aimlapi_base_url="https://legacy-compatible.example/v1",
        )

        self.assertEqual(
            resolve_aimlapi_base_url(settings),
            "https://legacy-compatible.example/v1",
        )

    def test_explicit_new_aiml_base_url_wins_over_legacy_override(self) -> None:
        settings = Settings(
            aiml_base_url="https://new-compatible.example/v1",
            aimlapi_base_url="https://legacy-compatible.example/v1",
        )

        self.assertEqual(
            resolve_aimlapi_base_url(settings),
            "https://new-compatible.example/v1",
        )

    def test_autonomous_role_provider_uses_legacy_aimlapi_override(self) -> None:
        settings = Settings(
            aiml_base_url=AIMLAPI_DEFAULT_BASE_URL,
            aimlapi_base_url="https://legacy-compatible.example/v1",
        )

        config = _provider_config_for_role(ROLE_DEFINITIONS["triage"], settings)

        self.assertEqual(config.name, "aimlapi")
        self.assertEqual(config.base_url, "https://legacy-compatible.example/v1")


if __name__ == "__main__":
    unittest.main()
