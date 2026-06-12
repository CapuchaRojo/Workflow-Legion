"""Deterministic Incident Commander Agent output for the demo incident."""

from agents.contracts import (
    AgentOutput,
    DEMO_INCIDENT_ID,
    EvidenceItem,
    require_demo_incident,
)


def build_mock_output(incident_id: str = DEMO_INCIDENT_ID) -> AgentOutput:
    """Produce the repeatable final command decision for the demo."""

    require_demo_incident(incident_id)

    return AgentOutput(
        incident_id=incident_id,
        agent_id="commander",
        agent_name="Incident Commander Agent",
        status="completed",
        severity="high",
        confidence=0.9,
        summary=(
            "Declare WL-INC-001 a high-severity incident. Contain FIN-042 and the "
            "j.morgan account immediately, preserve evidence, and investigate the "
            "48 MB transfer before making an external notification decision."
        ),
        findings=(
            "Triage identified a credible multi-signal compromise on a Finance asset.",
            "Threat intelligence found contextual risk but no conclusive malicious "
            "reputation for the destination.",
            "Forensics established a sequence consistent with collection and possible "
            "exfiltration.",
            "Compliance requires preservation and escalation while notification "
            "remains pending.",
        ),
        evidence=(
            EvidenceItem(
                kind="decision_basis",
                value="Triage + Threat Intel + Forensics + Compliance findings",
                assessment="Sufficient for containment; insufficient to confirm exposure.",
            ),
        ),
        recommended_actions=(
            "Isolate FIN-042 from the network while preserving evidence.",
            "Disable active j.morgan sessions and initiate credential reset.",
            "Block or closely monitor the destination across the environment.",
            "Preserve endpoint, identity, file, proxy, and Band audit records.",
            "Scope the 48 MB transfer and search for related activity.",
        ),
        mentions=(),
        handoff_to=(),
        band_message=(
            "[WL-INC-001][COMMANDER DECISION][HIGH] Authorize immediate containment: "
            "isolate FIN-042, disable active j.morgan sessions, preserve endpoint and "
            "Band audit evidence, and monitor/block 185.199.108.153. Investigate the "
            "48 MB transfer and related hosts. Data exposure and external notification "
            "remain pending forensic confirmation."
        ),
    )
