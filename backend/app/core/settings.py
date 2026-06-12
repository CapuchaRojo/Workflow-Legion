try:
    from pydantic_settings import BaseSettings
except ImportError:
    # FastAPI 0.94 uses Pydantic v1, where BaseSettings lives in pydantic.
    from pydantic import BaseSettings

class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "sqlite:///./workflow_legion.db"
    redis_url: str = "redis://localhost:6379/0"

    band_api_key: str | None = None
    band_base_url: str = "https://app.band.ai/api/v1"
    band_chat_id: str | None = None
    band_room_id: str | None = None
    band_default_mention_handles: str = "redhood"

    band_triage_agent_api_key: str | None = None
    band_threat_intel_agent_api_key: str | None = None
    band_forensics_agent_api_key: str | None = None
    band_compliance_agent_api_key: str | None = None
    band_commander_agent_api_key: str | None = None

    band_triage_handle: str = "@Triage"
    band_threat_intel_handle: str = "@ThreatIntel"
    band_forensics_handle: str = "@Forensics"
    band_compliance_handle: str = "@Compliance"
    band_commander_handle: str = "@Commander"

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_model: str | None = None
    anthropic_model: str | None = None

    featherless_api_key: str | None = None
    featherless_base_url: str = "https://api.featherless.ai/v1"
    featherless_model: str | None = None

    aimlapi_api_key: str | None = None
    aimlapi_base_url: str = "https://api.aimlapi.com/v1"
    aimlapi_model: str | None = None

    llm_provider: str = "openai"
    llm_fallback_provider: str = "featherless"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
