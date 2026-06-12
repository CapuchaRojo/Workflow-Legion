"""Deterministic Threat Intel Agent output for the demo incident."""

from agents.contracts import (
    AgentOutput,
    DEMO_INCIDENT_ID,
    EvidenceItem,
    require_demo_incident,
)


def build_mock_output(incident_id: str = DEMO_INCIDENT_ID) -> AgentOutput:
    """Enrich the synthetic indicators without relying on a live provider."""

    require_demo_incident(incident_id)

    return AgentOutput(
        incident_id=incident_id,
        agent_id="threat_intel",
        agent_name="Threat Intel Agent",
        status="completed",
        severity="high",
        confidence=0.78,
        summary=(
            "The destination IP is shared public infrastructure and is not "
            "malicious by reputation alone, but it is anomalous for FIN-042. "
            "The executable is absent from the mock approved-software inventory."
        ),
        findings=(
            "185.199.108.153 belongs to a shared public-hosting range, so the IP "
            "requires context rather than an automatic malicious verdict.",
            "FIN-042 has no expected business communication with the destination "
            "in the mock network baseline.",
            "invoice_update.exe has no match in the mock approved-software or "
            "known-good hash inventory.",
        ),
        evidence=(
            EvidenceItem(
                kind="ioc",
                value="185.199.108.153",
                assessment="Reputation inconclusive; behavior is anomalous for FIN-042.",
            ),
            EvidenceItem(
                kind="executable",
                value="invoice_update.exe",
                assessment="Unknown and unapproved in the deterministic inventory.",
            ),
        ),
        recommended_actions=(
            "Keep the destination under enhanced monitoring pending scoping.",
            "Collect the executable hash and preserve the binary for analysis.",
            "Correlate the destination with DNS, proxy, and firewall telemetry.",
        ),
        mentions=("compliance",),
        handoff_to=("compliance",),
        band_message=(
            "[WL-INC-001][THREAT-INTEL] Enrichment complete. 185.199.108.153 is "
            "shared public infrastructure, so reputation is inconclusive, but the "
            "connection is anomalous for FIN-042. invoice_update.exe is not in the "
            "approved-software inventory. Confidence: 0.78. @ComplianceAgent please "
            "review retention and escalation requirements while Forensics confirms "
            "the scope."
        ),
    )
