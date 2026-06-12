"""Deterministic Alert Triage Agent output for the demo incident."""

from agents.contracts import (
    AgentOutput,
    DEMO_INCIDENT_ID,
    EvidenceItem,
    require_demo_incident,
)


def build_mock_output(incident_id: str = DEMO_INCIDENT_ID) -> AgentOutput:
    """Classify the alert and prepare the first visible Band handoffs."""

    require_demo_incident(incident_id)

    return AgentOutput(
        incident_id=incident_id,
        agent_id="triage",
        agent_name="Alert Triage Agent",
        status="completed",
        severity="high",
        confidence=0.91,
        summary=(
            "Suspicious PowerShell execution on FIN-042 is followed by an "
            "unapproved executable, repeated login failures, sensitive finance "
            "file access, and unusual outbound traffic."
        ),
        findings=(
            "The activity combines execution, credential-access, collection, and "
            "possible exfiltration signals.",
            "The affected asset belongs to Finance and the accessed workbook is "
            "business-sensitive.",
            "Data exfiltration remains suspected, not confirmed.",
        ),
        evidence=(
            EvidenceItem(
                kind="process",
                value="powershell.exe -> invoice_update.exe",
                assessment="Suspicious parent-child execution chain.",
            ),
            EvidenceItem(
                kind="network",
                value="185.199.108.153",
                assessment="Unknown destination in the incident context.",
            ),
            EvidenceItem(
                kind="file",
                value="finance_q4_forecast.xlsx",
                assessment="Sensitive finance file accessed before outbound traffic.",
            ),
        ),
        recommended_actions=(
            "Begin endpoint containment preparation for FIN-042.",
            "Enrich the destination IP and executable indicators.",
            "Reconstruct the endpoint and network timeline.",
        ),
        mentions=("threat_intel", "forensics"),
        handoff_to=("threat_intel", "forensics"),
        band_message=(
            "[WL-INC-001][TRIAGE][HIGH] Suspicious PowerShell activity on FIN-042 "
            "was followed by invoice_update.exe, failed logins, access to "
            "finance_q4_forecast.xlsx, and unusual outbound traffic. "
            "@ThreatIntelAgent please enrich 185.199.108.153 and the executable. "
            "@ForensicsAgent please reconstruct the endpoint/network timeline and "
            "assess possible exfiltration."
        ),
    )
