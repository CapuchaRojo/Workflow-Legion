"""Lookup helpers for one agent output at a time.

This module does not execute the workflow. Band messages and mentions remain
the collaboration and handoff mechanism between agents.
"""

from collections.abc import Callable

from agents.commander_agent import build_mock_output as build_commander_output
from agents.compliance_agent import build_mock_output as build_compliance_output
from agents.contracts import AgentOutput, DEMO_INCIDENT_ID
from agents.forensics_agent import build_mock_output as build_forensics_output
from agents.threat_intel_agent import build_mock_output as build_threat_intel_output
from agents.triage_agent import build_mock_output as build_triage_output


AgentBuilder = Callable[[str], AgentOutput]

_BUILDERS: dict[str, AgentBuilder] = {
    "triage": build_triage_output,
    "threat_intel": build_threat_intel_output,
    "forensics": build_forensics_output,
    "compliance": build_compliance_output,
    "commander": build_commander_output,
}

AGENT_IDS = tuple(_BUILDERS)


def get_mock_agent_output(
    agent_id: str, incident_id: str = DEMO_INCIDENT_ID
) -> AgentOutput:
    """Return a deterministic output for the requested agent."""

    normalized_agent_id = agent_id.lower().strip().replace("-", "_")

    try:
        builder = _BUILDERS[normalized_agent_id]
    except KeyError as exc:
        supported = ", ".join(AGENT_IDS)
        raise ValueError(
            f"Unknown agent '{agent_id}'. Supported agents: {supported}."
        ) from exc

    return builder(incident_id)
