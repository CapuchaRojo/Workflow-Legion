from enum import Enum

from pydantic import BaseModel

from app.core.settings import settings


class LLMProvider(str, Enum):
    OPENAI = "openai"
    FEATHERLESS = "featherless"
    AIML = "aiml"
    AIMLAPI = "aimlapi"
    ANTHROPIC = "anthropic"


class ProviderConfig(BaseModel):
    name: str
    api_key: str | None
    base_url: str | None = None
    model: str | None = None


def get_provider_config(provider: str) -> ProviderConfig:
    provider = provider.lower().strip()

    if provider == LLMProvider.FEATHERLESS:
        return ProviderConfig(
            name="featherless",
            api_key=getattr(settings, "featherless_api_key", None),
            base_url=getattr(settings, "featherless_base_url", "https://api.featherless.ai/v1"),
            model=getattr(settings, "featherless_model", None),
        )

    if provider in (LLMProvider.AIML, LLMProvider.AIMLAPI, "aiml_api"):
        return ProviderConfig(
            name="aimlapi",
            api_key=(
                getattr(settings, "aiml_api_key", None)
                or getattr(settings, "aimlapi_api_key", None)
            ),
            base_url=(
                getattr(settings, "aiml_base_url", None)
                or getattr(settings, "aimlapi_base_url", "https://api.aimlapi.com/v1")
            ),
            model=(
                getattr(settings, "aiml_model", None)
                or getattr(settings, "aimlapi_model", None)
            ),
        )

    if provider == LLMProvider.ANTHROPIC:
        return ProviderConfig(
            name="anthropic",
            api_key=getattr(settings, "anthropic_api_key", None),
            model=getattr(settings, "anthropic_model", None),
        )

    return ProviderConfig(
        name="openai",
        api_key=getattr(settings, "openai_api_key", None),
        model=getattr(settings, "openai_model", None),
    )
