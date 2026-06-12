"""Tests for settings and provider router imports."""

import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.llm_provider_router import get_provider_config  # noqa: E402


class ProviderRouterTests(unittest.TestCase):
    def test_declared_providers_load_without_credentials(self) -> None:
        expected = {
            "openai": None,
            "anthropic": None,
            "featherless": "https://api.featherless.ai/v1",
            "aimlapi": "https://api.aimlapi.com/v1",
        }

        for provider, base_url in expected.items():
            config = get_provider_config(provider)
            self.assertEqual(config.name, provider)
            self.assertEqual(config.base_url, base_url)


if __name__ == "__main__":
    unittest.main()
