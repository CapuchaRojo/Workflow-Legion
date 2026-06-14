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
            f"Initial triage classifies {incident.incident_id} as high severity "
            f"for {incident.title} affecting {incident.affected_host}, user "
            f"{incident.affected_user}, and {incident.department}. Breach, "
            "exfiltration, or compromise remain unconfirmed pending downstream "
            f"review. Scenario summary: {incident.summary}"
        ),
        evidence=[
            EvidenceItem(
                evidence_id="EV-TG-001",
                category="alert",
                summary=(
                    f"{incident.title} alert on {incident.affected_host} for "
                    f"{incident.affected_user}; indicators include "
                    f"{_indicator_sentence(incident)}."
                ),
                source="Scenario alert",
                confidence="high",
            )
        ],
        recommended_actions=[
            f"Preserve host telemetry for {incident.affected_host}.",
            "Request IOC enrichment and endpoint timeline review.",
            "Prepare containment approval if downstream review confirms scope.",
        ],
        band_message=(
            f"{band_mention(threat_handle)} {band_mention(forensics_handle)} "
            f"{incident.incident_id} triage: {incident.title} on "
            f"{incident.affected_host}, user {incident.affected_user}, "
            f"{incident.department}. Please enrich indicators and build the "
            "endpoint, identity, and network timeline."
        ),
    )


def build_threat_intel_finding(
    incident: IncidentState,
    compliance_handle: str,
) -> AgentFinding:
    primary_indicator = _primary_indicator(incident)
    secondary_indicator = _secondary_indicator(incident)
    return AgentFinding(
        agent="threat_intel",
        status="complete",
        severity="high",
        confidence="medium",
        summary=(
            f"Threat Intel reviewed {incident.incident_id} indicators for "
            f"{incident.title}. {primary_indicator} is suspicious by context "
            "within the supplied scenario evidence, but no live IOC lookup was "
            "performed and maliciousness is not independently confirmed."
        ),
        evidence=[
            EvidenceItem(
                evidence_id="EV-TI-001",
                category="ioc",
                summary=(
                    f"{incident.affected_host} indicator requires context-based "
                    f"review: {primary_indicator}."
                ),
                source="Scenario IOC review",
                confidence="medium",
            ),
            EvidenceItem(
                evidence_id="EV-TI-002",
                category="indicator",
                summary=(
                    f"Additional {incident.department} context for "
                    f"{incident.affected_user}: {secondary_indicator}."
                ),
                source="Scenario indicator heuristic",
                confidence="medium",
            ),
        ],
        recommended_actions=[
            f"Monitor or restrict activity tied to {primary_indicator}.",
            "Preserve indicator details for controlled enrichment if approved.",
            f"Ask Compliance to assess {incident.department} data exposure risk.",
        ],
        band_message=(
            f"{band_mention(compliance_handle)} Threat Intel update for "
            f"{incident.incident_id}: indicators are suspicious by scenario "
            "context, not conclusive alone. Compliance should review the "
            f"{incident.department} exposure risk."
        ),
    )


def build_forensics_finding(
    incident: IncidentState,
    compliance_handle: str,
) -> AgentFinding:
    timeline = _build_forensics_timeline(incident)
    return AgentFinding(
        agent="forensics",
        status="complete",
        severity="high",
        confidence="high",
        summary=(
            f"Forensics reconstructed a scenario timeline for {incident.incident_id}: "
            f"{incident.title} involving {incident.affected_host}, "
            f"{incident.affected_user}, and indicators including "
            f"{_indicator_sentence(incident)}."
        ),
        evidence=[
            EvidenceItem(
                evidence_id="EV-FO-001",
                category=_activity_category(incident),
                summary=(
                    f"{_process_observable(incident)} observed on "
                    f"{incident.affected_host} for {incident.affected_user}."
                ),
                source="Synthetic endpoint log",
                confidence="high",
            ),
            EvidenceItem(
                evidence_id="EV-FO-002",
                category="file_access",
                summary=(
                    f"{_file_observable(incident)} was involved during the "
                    f"{incident.department} suspicious sequence."
                ),
                source="Synthetic audit log",
                confidence="high",
            ),
            EvidenceItem(
                evidence_id="EV-FO-003",
                category="network",
                summary=(
                    f"Follow-on network or access activity for "
                    f"{incident.affected_host} included {_network_observable(incident)}."
                ),
                source="Synthetic proxy log",
                confidence="medium",
            ),
        ],
        timeline=timeline,
        recommended_actions=_forensics_actions(incident),
        band_message=(
            f"{band_mention(compliance_handle)} Forensics update for "
            f"{incident.incident_id}: evidence supports high-risk suspicious "
            f"activity on {incident.affected_host}; exposure or compromise "
            "remains suspected until scope is validated."
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
            f"Compliance review flags audit sensitivity for {incident.incident_id} "
            f"because the affected user and assets belong to {incident.department}. "
            "This is not legal or regulatory advice; evidence retention and "
            "management escalation are recommended while scope is validated."
        ),
        evidence=[
            EvidenceItem(
                evidence_id="EV-CO-001",
                category="governance",
                summary=(
                    f"{incident.department} activity involving "
                    f"{incident.affected_user} on {incident.affected_host} creates "
                    "potential data exposure review needs."
                ),
                source="Compliance review",
                confidence="medium",
            )
        ],
        recommended_actions=_compliance_actions(incident),
        band_message=(
            f"{band_mention(commander_handle)} Compliance update for "
            f"{incident.incident_id}: retain evidence, escalate internally, and "
            "classify as high severity pending scope confirmation."
        ),
    )


def build_commander_finding(incident: IncidentState) -> AgentFinding:
    return AgentFinding(
        agent="commander",
        status="complete",
        severity="high",
        confidence="high",
        summary=(
            f"Commander decision: treat {incident.incident_id} as a high-severity "
            f"suspected incident involving {incident.title} for "
            f"{incident.affected_host}. Contain the affected surface, protect "
            "credentials, and continue scope validation."
        ),
        recommended_actions=_commander_actions(incident),
        band_message=(
            f"Commander final decision for {incident.incident_id}: HIGH severity. "
            f"Contain {incident.affected_host}, protect {incident.affected_user}, "
            "preserve evidence, and continue scope validation before external "
            "claims or notifications."
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


def _indicator_sentence(incident: IncidentState, limit: int = 3) -> str:
    return "; ".join(
        f"{_display_key(key)}={value}"
        for key, value in list(incident.indicators.items())[:limit]
    )


def _primary_indicator(incident: IncidentState) -> str:
    return _first_indicator(
        incident,
        (
            "destination_ip",
            "source_ip",
            "domain",
            "sender_domain",
            "bucket",
            "process",
            "invoice_file",
            "exposed_file",
        ),
    )


def _secondary_indicator(incident: IncidentState) -> str:
    primary = _primary_indicator(incident)
    for key, value in incident.indicators.items():
        formatted = f"{_display_key(key)}={value}"
        if formatted != primary:
            return formatted
    return primary


def _process_observable(incident: IncidentState) -> str:
    return _first_indicator(
        incident,
        (
            "process",
            "file",
            "sender_domain",
            "bucket",
            "domain",
            "failed_login_count",
            "access_pattern",
        ),
    )


def _file_observable(incident: IncidentState) -> str:
    return _first_indicator(
        incident,
        (
            "target_file",
            "invoice_file",
            "exposed_file",
            "object_prefix",
            "mailbox_rule",
            "mfa_pushes",
            "persistence",
        ),
    )


def _network_observable(incident: IncidentState) -> str:
    return _first_indicator(
        incident,
        (
            "destination_ip",
            "source_ip",
            "domain",
            "sender_domain",
            "bucket",
            "access_pattern",
            "dns_rate",
        ),
    )


def _first_indicator(incident: IncidentState, preferred_keys: tuple[str, ...]) -> str:
    for key in preferred_keys:
        value = incident.indicators.get(key)
        if value:
            return f"{_display_key(key)}={value}"

    key, value = next(iter(incident.indicators.items()))
    return f"{_display_key(key)}={value}"


def _indicator_value(incident: IncidentState, key: str) -> str | None:
    value = incident.indicators.get(key)
    return str(value) if value else None


def _display_key(key: str) -> str:
    return key.replace("_", " ")


def _friendly_process(process: str | None) -> str:
    if not process:
        return "Scenario activity"
    if process.lower() == "powershell.exe":
        return "PowerShell"
    return process


def _timeline_auth_activity(incident: IncidentState) -> str:
    failed_count = _indicator_value(incident, "failed_login_count")
    mfa_pushes = _indicator_value(incident, "mfa_pushes")
    if failed_count and mfa_pushes:
        return f"{failed_count} failed logins and {mfa_pushes} observed"
    if incident.incident_id == "WL-INC-001":
        return "Multiple failed logins observed"
    if _indicator_value(incident, "mailbox_rule"):
        return "Mailbox forwarding behavior observed"
    if _indicator_value(incident, "public_acl"):
        return "Public storage ACL observed"
    if _indicator_value(incident, "dns_rate"):
        return "Periodic DNS lookup pattern observed"
    return f"{incident.affected_user} activity reviewed"


def _timeline_asset_activity(incident: IncidentState) -> str:
    target_file = _indicator_value(incident, "target_file")
    if target_file:
        return f"{target_file} accessed"
    invoice_file = _indicator_value(incident, "invoice_file")
    if invoice_file:
        return f"{invoice_file} payment request reviewed"
    exposed_file = _indicator_value(incident, "exposed_file")
    if exposed_file:
        return f"{exposed_file} exposure reviewed"
    persistence = _indicator_value(incident, "persistence")
    if persistence:
        return persistence.capitalize()
    return f"{incident.department} evidence reviewed"


def _timeline_network_activity(incident: IncidentState) -> str:
    destination_ip = _indicator_value(incident, "destination_ip")
    if destination_ip:
        return f"Outbound traffic to {destination_ip}"
    source_ip = _indicator_value(incident, "source_ip")
    if source_ip:
        return f"Authentication traffic from {source_ip}"
    domain = _indicator_value(incident, "domain")
    if domain:
        return f"DNS or outbound traffic to {domain}"
    sender_domain = _indicator_value(incident, "sender_domain")
    if sender_domain:
        return f"Mail activity involving {sender_domain}"
    access_pattern = _indicator_value(incident, "access_pattern")
    if access_pattern:
        return f"Access pattern observed: {access_pattern}"
    return f"Network or access pattern reviewed for {incident.affected_host}"


def _activity_category(incident: IncidentState) -> str:
    if _indicator_value(incident, "process") or _indicator_value(incident, "file"):
        return "process"
    if _indicator_value(incident, "failed_login_count") or _indicator_value(
        incident,
        "impossible_travel",
    ):
        return "authentication"
    if _indicator_value(incident, "sender_domain") or _indicator_value(
        incident,
        "mailbox_rule",
    ):
        return "mailbox"
    if _indicator_value(incident, "bucket") or _indicator_value(
        incident,
        "public_acl",
    ):
        return "storage"
    if _indicator_value(incident, "dns_rate") or _indicator_value(incident, "domain"):
        return "dns"
    return "activity"


def _build_forensics_timeline(incident: IncidentState) -> list[TimelineEvent]:
    process = _friendly_process(_indicator_value(incident, "process"))
    return [
        TimelineEvent(
            order=1,
            time="09:14",
            actor=incident.affected_host,
            action=(
                f"{process} process started"
                if _indicator_value(incident, "process")
                else f"{incident.title} activity observed"
            ),
            significance="Suspicious process, identity, or access activity begins.",
        ),
        TimelineEvent(
            order=2,
            time="09:16",
            actor=incident.affected_user,
            action=_timeline_auth_activity(incident),
            significance="Potential account misuse or suspicious workflow activity.",
        ),
        TimelineEvent(
            order=3,
            time="09:19",
            actor=incident.affected_host,
            action=_timeline_asset_activity(incident),
            significance=f"{incident.department} data or workflow evidence touched.",
        ),
        TimelineEvent(
            order=4,
            time="09:22",
            actor=incident.affected_host,
            action=_timeline_network_activity(incident),
            significance="Possible exposure path requires containment review.",
        ),
    ]


def _forensics_actions(incident: IncidentState) -> list[str]:
    scenario_actions = {
        "WL-INC-002": [
            "Disable the suspicious session for s.patel pending commander decision.",
            "Reset s.patel credentials and review active sessions.",
            "Preserve identity logs and MFA fatigue evidence.",
        ],
        "WL-INC-003": [
            "Preserve a.lee mailbox evidence and mail-security logs.",
            "Disable the external forwarding rule pending commander decision.",
            "Verify the payment change request out-of-band with the vendor.",
        ],
        "WL-INC-004": [
            "Revoke anonymous read access on customer-export-archive pending commander decision.",
            "Rotate svc-data-export credentials after preserving evidence.",
            "Preserve cloud storage access logs for exports/q4/.",
        ],
        "WL-INC-005": [
            "Isolate ENG-117 from the network pending commander decision.",
            "Preserve DNS and process telemetry for updater_service.exe.",
            "Disable the suspicious scheduled task persistence mechanism.",
        ],
    }
    return scenario_actions.get(
        incident.incident_id,
        [
            f"Isolate {incident.affected_host} from the network pending commander decision.",
            f"Reset {incident.affected_user} credentials and review active sessions.",
            "Preserve endpoint, identity, file, and network evidence.",
        ],
    )


def _compliance_actions(incident: IncidentState) -> list[str]:
    scope_word = (
        "exfiltration"
        if incident.incident_id == "WL-INC-001"
        else "exposure"
    )
    return [
        "Open an evidence retention record.",
        f"Notify {incident.department} leadership and security management.",
        f"Defer external notification until {scope_word} scope is confirmed.",
    ]


def _commander_actions(incident: IncidentState) -> list[str]:
    scenario_actions = {
        "WL-INC-002": [
            "Disable the suspicious s.patel session immediately.",
            "Reset s.patel credentials and revoke active sessions.",
            "Review MFA fatigue patterns and denied push prompts.",
            "Preserve identity, MFA, and source IP evidence.",
            "Run a second validation pass before final external reporting decisions.",
        ],
        "WL-INC-003": [
            "Preserve a.lee mailbox and message trace evidence.",
            "Disable the external forwarding rule immediately.",
            "Verify the payment change request out-of-band before any payment action.",
            "Preserve invoice, sender-domain, and mailbox-rule evidence.",
            "Run a second validation pass before final external reporting decisions.",
        ],
        "WL-INC-004": [
            "Revoke anonymous read access on customer-export-archive immediately.",
            "Rotate svc-data-export credentials after evidence preservation.",
            "Preserve cloud storage access logs and object metadata.",
            "Review exports/q4/ for potential customer contact data exposure.",
            "Run a second validation pass before final external reporting decisions.",
        ],
        "WL-INC-005": [
            "Isolate ENG-117 immediately.",
            "Preserve DNS and process telemetry for updater_service.exe.",
            "Disable the suspicious scheduled task persistence mechanism.",
            "Monitor or restrict destination ip=198.51.100.42 during investigation.",
            "Run a second validation pass before final external reporting decisions.",
        ],
    }
    return scenario_actions.get(
        incident.incident_id,
        [
            f"Isolate {incident.affected_host} immediately.",
            f"Reset {incident.affected_user} credentials and revoke active sessions.",
            f"Monitor or restrict {_primary_indicator(incident)} during investigation.",
            "Preserve endpoint, identity, file, and network evidence.",
            "Run a second validation pass before final external reporting decisions.",
        ],
    )
