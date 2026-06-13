from dataclasses import dataclass

from app.core.settings import Settings
from app.services.band_client import BandClient, normalize_mention_handle


@dataclass(frozen=True)
class BandRemoteAgent:
    role: str
    display_name: str
    handle: str
    agent_id: str | None
    agent_api_key: str | None

    @property
    def configured(self) -> bool:
        return bool(self.agent_api_key)


def build_band_remote_agent_registry(settings: Settings) -> dict[str, BandRemoteAgent]:
    """Build role-specific Band remote agent config without exposing secrets.

    The triage role supports legacy aliases so existing smoke-test behavior
    continues while the project moves toward one Band identity per agent role.
    """

    triage_agent_id = settings.band_triage_agent_id or settings.band_agent_id
    triage_api_key = settings.band_triage_agent_api_key or settings.band_api_key

    return {
        "triage": BandRemoteAgent(
            role="triage",
            display_name="Workflow Triage Remote Agent",
            handle=_clean_handle(settings.band_triage_handle),
            agent_id=triage_agent_id,
            agent_api_key=triage_api_key,
        ),
        "threat_intel": BandRemoteAgent(
            role="threat_intel",
            display_name="Workflow Threat Intel Agent",
            handle=_clean_handle(settings.band_threat_intel_handle),
            agent_id=settings.band_threat_intel_agent_id,
            agent_api_key=settings.band_threat_intel_agent_api_key,
        ),
        "forensics": BandRemoteAgent(
            role="forensics",
            display_name="Workflow Forensics Agent",
            handle=_clean_handle(settings.band_forensics_handle),
            agent_id=settings.band_forensics_agent_id,
            agent_api_key=settings.band_forensics_agent_api_key,
        ),
        "compliance": BandRemoteAgent(
            role="compliance",
            display_name="Workflow Compliance Agent",
            handle=_clean_handle(settings.band_compliance_handle),
            agent_id=settings.band_compliance_agent_id,
            agent_api_key=settings.band_compliance_agent_api_key,
        ),
        "commander": BandRemoteAgent(
            role="commander",
            display_name="Workflow Incident Commander Agent",
            handle=_clean_handle(settings.band_commander_handle),
            agent_id=settings.band_commander_agent_id,
            agent_api_key=settings.band_commander_agent_api_key,
        ),
    }


def build_band_client_for_agent(settings: Settings, agent: BandRemoteAgent) -> BandClient:
    return BandClient(
        base_url=settings.band_base_url,
        agent_api_key=agent.agent_api_key,
    )


def _clean_handle(handle: str) -> str:
    return normalize_mention_handle(handle)