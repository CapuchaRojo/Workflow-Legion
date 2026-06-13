from app.models.incident import AgentFinding, EvidenceItem, IncidentState, TimelineEvent


def band_mention(handle: str) -> str:
    """Render a configured Band handle as a visible @mention.

    Handles should be stored in env/config without a leading @, but Band message
    content needs the visible @ token so the mention can resolve cleanly.
    """

    return f"@{str(handle).strip().removeprefix('@')}"


def build_triage_finding(
    incident: IncidentState,
    threat_handle: str,
    forensics_handle: str,
) -> AgentFinding:
    return AgentFinding(
        agent="triage",
        status="complete",
        severity="high",
        confidence="high",
        summary=(
            "Initial triage classifies WL-INC-001 as high severity due to suspicious "
            "PowerShell activity on a finance endpoint and possible sensitive file access."
        ),
        evidence=[
            EvidenceItem(
                evidence_id="EV-TG-001",
                category="alert",
                summary="PowerShell launched a suspicious executable on FIN-042.",
                source="EDR alert",
                confidence="high",
            )
        ],
        recommended_actions=[
            "Preserve host telemetry for FIN-042.",
            "Request IOC enrichment and endpoint timeline review.",
            "Prepare containment approval if exfiltration is confirmed.",
        ],
        band_message=(
            f"{band_mention(threat_handle)} {band_mention(forensics_handle)} "
            "WL-INC-001 triage: suspicious PowerShell activity on FIN-042, "
            "user j.morgan, possible data exfiltration. Please enrich indicators "
            "and build the endpoint/network timeline."
        ),
    )


def build_threat_intel_finding(
    incident: IncidentState,
    compliance_handle: str,
) -> AgentFinding:
    destination_ip = incident.indicators["destination_ip"]
    return AgentFinding(
        agent="threat_intel",
        status="complete",
        severity="high",
        confidence="medium",
        summary=(
            f"Threat Intel found the destination IP {destination_ip} is associated with "
            "public hosting infrastructure, which is not inherently malicious but is unusual "
            "for finance workstation egress during suspicious process execution."
        ),
        evidence=[
            EvidenceItem(
                evidence_id="EV-TI-001",
                category="ioc",
                summary=f"Outbound destination {destination_ip} requires context-based review.",
                source="Mock IOC enrichment",
                confidence="medium",
            ),
            EvidenceItem(
                evidence_id="EV-TI-002",
                category="file",
                summary="invoice_update.exe matches a suspicious lure-style filename.",
                source="Mock filename heuristic",
                confidence="medium",
            ),
        ],
        recommended_actions=[
            "Block or monitor outbound traffic to the destination during investigation.",
            "Submit invoice_update.exe hash to sandbox when available.",
            "Ask Compliance to assess finance data reporting obligations.",
        ],
        band_message=(
            f"{band_mention(compliance_handle)} Threat Intel update for WL-INC-001: "
            "IOCs are suspicious by context, not conclusive alone. Finance data "
            "access raises audit and reporting review needs."
        ),
    )


def build_forensics_finding(
    incident: IncidentState,
    compliance_handle: str,
) -> AgentFinding:
    return AgentFinding(
        agent="forensics",
        status="complete",
        severity="high",
        confidence="high",
        summary=(
            "Forensics reconstructed a suspicious sequence: PowerShell execution, failed "
            "login attempts, finance file access, and outbound network activity."
        ),
        evidence=[
            EvidenceItem(
                evidence_id="EV-FO-001",
                category="process",
                summary="powershell.exe launched invoice_update.exe on FIN-042.",
                source="Synthetic endpoint log",
                confidence="high",
            ),
            EvidenceItem(
                evidence_id="EV-FO-002",
                category="file_access",
                summary="finance_q4_forecast.xlsx was accessed after suspicious execution.",
                source="Synthetic file audit log",
                confidence="high",
            ),
            EvidenceItem(
                evidence_id="EV-FO-003",
                category="network",
                summary="Outbound connection followed sensitive file access.",
                source="Synthetic proxy log",
                confidence="medium",
            ),
        ],
        timeline=[
            TimelineEvent(
                order=1,
                time="09:14",
                actor="FIN-042",
                action="PowerShell process started",
                significance="Suspicious script execution begins.",
            ),
            TimelineEvent(
                order=2,
                time="09:16",
                actor="j.morgan",
                action="Multiple failed logins observed",
                significance="Potential credential misuse or lateral movement attempt.",
            ),
            TimelineEvent(
                order=3,
                time="09:19",
                actor="FIN-042",
                action="finance_q4_forecast.xlsx accessed",
                significance="Sensitive finance data touched during suspicious session.",
            ),
            TimelineEvent(
                order=4,
                time="09:22",
                actor="FIN-042",
                action="Outbound traffic to 185.199.108.153",
                significance="Possible exfiltration path requires containment.",
            ),
        ],
        recommended_actions=[
            "Isolate FIN-042 from the network pending commander decision.",
            "Reset j.morgan credentials and review active sessions.",
            "Preserve endpoint image and proxy logs.",
        ],
        band_message=(
            f"{band_mention(compliance_handle)} Forensics update for WL-INC-001: "
            "evidence supports high-risk suspicious activity with possible finance "
            "data exposure."
        ),
    )


def build_compliance_finding(
    incident: IncidentState,
    commander_handle: str,
) -> AgentFinding:
    return AgentFinding(
        agent="compliance",
        status="complete",
        severity="high",
        confidence="medium",
        summary=(
            "Compliance review flags audit sensitivity because the impacted user and file "
            "belong to Finance. Reporting is not confirmed, but evidence retention and "
            "management escalation are required."
        ),
        evidence=[
            EvidenceItem(
                evidence_id="EV-CO-001",
                category="governance",
                summary="Finance file access plus outbound traffic creates potential data exposure.",
                source="Compliance review",
                confidence="medium",
            )
        ],
        recommended_actions=[
            "Open an evidence retention record.",
            "Notify finance leadership and security management.",
            "Defer external notification until exfiltration scope is confirmed.",
        ],
        band_message=(
            f"{band_mention(commander_handle)} Compliance update for WL-INC-001: "
            "retain evidence, escalate internally, and classify as high severity "
            "pending scope confirmation."
        ),
    )


def build_commander_finding(incident: IncidentState) -> AgentFinding:
    return AgentFinding(
        agent="commander",
        status="complete",
        severity="high",
        confidence="high",
        summary=(
            "Commander decision: treat WL-INC-001 as a high-severity suspected compromise "
            "with potential finance data exposure. Contain host, protect credentials, and "
            "continue scope validation."
        ),
        recommended_actions=[
            "Isolate FIN-042 immediately.",
            "Reset j.morgan credentials and revoke active sessions.",
            "Block suspicious outbound destination while investigating.",
            "Preserve endpoint, identity, file, and network evidence.",
            "Run a second validation pass before final external reporting decisions.",
        ],
        band_message=(
            "Commander final decision for WL-INC-001: HIGH severity. Isolate FIN-042, "
            "reset j.morgan credentials, preserve evidence, and continue exfiltration scoping."
        ),
    )


def run_deterministic_workflow(
    incident: IncidentState,
    threat_handle: str,
    forensics_handle: str,
    compliance_handle: str,
    commander_handle: str,
) -> list[AgentFinding]:
    findings = [
        build_triage_finding(incident, threat_handle, forensics_handle),
        build_threat_intel_finding(incident, compliance_handle),
        build_forensics_finding(incident, compliance_handle),
        build_compliance_finding(incident, commander_handle),
        build_commander_finding(incident),
    ]
    return findings
