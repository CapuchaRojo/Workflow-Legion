"""Deterministic Compliance Agent output for the demo incident."""

from agents.contracts import (
    AgentOutput,
    DEMO_INCIDENT_ID,
    EvidenceItem,
    require_demo_incident,
)


def build_mock_output(incident_id: str = DEMO_INCIDENT_ID) -> AgentOutput:
    """Prepare audit and escalation guidance from the synthetic findings."""

    require_demo_incident(incident_id)

    return AgentOutput(
        incident_id=incident_id,
        agent_id="compliance",
        agent_name="Compliance Agent",
        status="completed",
        severity="high",
        confidence=0.84,
        summary=(
            "The incident involves possible unauthorized access to sensitive "
            "finance data. Evidence preservation and documented escalation are "
            "required; external notification cannot be decided until data exposure "
            "is confirmed."
        ),
        findings=(
            "The Band room audit trail should be retained with endpoint, identity, "
            "network, and file-access evidence.",
            "The finance workbook may contain sensitive business information, so "
            "scope and ownership must be documented.",
            "Regulatory or contractual notification thresholds are not yet met by "
            "the available facts because exposure is unconfirmed.",
        ),
        evidence=(
            EvidenceItem(
                kind="audit",
                value="Band collaboration trail",
                assessment="Preserve messages, mentions, decisions, and timestamps.",
            ),
            EvidenceItem(
                kind="data_scope",
                value="finance_q4_forecast.xlsx",
                assessment="Confirm classification, ownership, and transferred content.",
            ),
        ),
        recommended_actions=(
            "Open a formal incident record and preserve chain-of-custody metadata.",
            "Notify Finance data ownership and the internal security escalation path.",
            "Reassess notification duties after transferred content is confirmed.",
        ),
        mentions=("commander",),
        handoff_to=("commander",),
        band_message=(
            "[WL-INC-001][COMPLIANCE] Treat this as a documented high-severity "
            "security incident involving possible finance-data exposure. Preserve "
            "the Band audit trail and endpoint/network evidence. External "
            "notification remains pending confirmation of transferred content. "
            "@IncidentCommanderAgent findings are ready for a containment decision."
        ),
    )
