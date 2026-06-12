"""Deterministic Forensics Agent output for the demo incident."""

from agents.contracts import (
    AgentOutput,
    DEMO_INCIDENT_ID,
    EvidenceItem,
    require_demo_incident,
)


def build_mock_output(incident_id: str = DEMO_INCIDENT_ID) -> AgentOutput:
    """Build a repeatable synthetic timeline from endpoint and network evidence."""

    require_demo_incident(incident_id)

    return AgentOutput(
        incident_id=incident_id,
        agent_id="forensics",
        agent_name="Forensics Agent",
        status="completed",
        severity="high",
        confidence=0.88,
        summary=(
            "Endpoint and network evidence forms a coherent sequence from "
            "PowerShell execution to sensitive file access and outbound transfer. "
            "The sequence supports possible exfiltration but does not prove content "
            "delivery."
        ),
        findings=(
            "PowerShell launched invoice_update.exe before the credential and file "
            "activity.",
            "finance_q4_forecast.xlsx was accessed three minutes before the outbound "
            "transfer began.",
            "Approximately 48 MB left FIN-042 during the suspicious session.",
        ),
        evidence=(
            EvidenceItem(
                kind="timeline",
                value="powershell.exe launched invoice_update.exe",
                assessment="Initial suspicious execution.",
                timestamp="2026-06-12T10:14:22Z",
            ),
            EvidenceItem(
                kind="timeline",
                value="Six failed login attempts for j.morgan",
                assessment="Possible credential probing or session instability.",
                timestamp="2026-06-12T10:16:03Z",
            ),
            EvidenceItem(
                kind="timeline",
                value="finance_q4_forecast.xlsx opened",
                assessment="Sensitive file collection signal.",
                timestamp="2026-06-12T10:18:41Z",
            ),
            EvidenceItem(
                kind="timeline",
                value="48 MB outbound to 185.199.108.153",
                assessment="Possible exfiltration event requiring packet/proxy review.",
                timestamp="2026-06-12T10:21:17Z",
            ),
        ),
        recommended_actions=(
            "Isolate FIN-042 while preserving volatile evidence.",
            "Acquire endpoint telemetry and the suspicious executable.",
            "Review proxy or packet data to determine transferred content.",
        ),
        mentions=("compliance",),
        handoff_to=("compliance",),
        band_message=(
            "[WL-INC-001][FORENSICS] Timeline complete: PowerShell launched "
            "invoice_update.exe at 10:14Z; six failed logins followed; "
            "finance_q4_forecast.xlsx was opened at 10:18Z; 48 MB was sent to "
            "185.199.108.153 at 10:21Z. Possible exfiltration is supported but not "
            "yet confirmed. @ComplianceAgent please assess audit, retention, and "
            "notification implications."
        ),
    )
