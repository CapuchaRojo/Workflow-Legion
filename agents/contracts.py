"""Shared structured output contracts for Workflow Legion agents."""

from dataclasses import asdict, dataclass
from typing import Any


DEMO_INCIDENT_ID = "WL-INC-001"


@dataclass(frozen=True)
class EvidenceItem:
    """One deterministic evidence item attached to an agent finding."""

    kind: str
    value: str
    assessment: str
    timestamp: str | None = None


@dataclass(frozen=True)
class AgentOutput:
    """Serializable output that a Band integration can post and persist."""

    incident_id: str
    agent_id: str
    agent_name: str
    status: str
    severity: str
    confidence: float
    summary: str
    findings: tuple[str, ...]
    evidence: tuple[EvidenceItem, ...]
    recommended_actions: tuple[str, ...]
    mentions: tuple[str, ...]
    handoff_to: tuple[str, ...]
    band_message: str
    mode: str = "deterministic_mock"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)


def require_demo_incident(incident_id: str) -> None:
    """Keep mock behavior explicit and deterministic for the demo incident."""

    if incident_id != DEMO_INCIDENT_ID:
        raise ValueError(
            f"Deterministic mock output is only defined for {DEMO_INCIDENT_ID}."
        )
