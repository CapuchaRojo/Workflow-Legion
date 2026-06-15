from app.models.incident import AgentFinding, EvidenceItem, IncidentState, TimelineEvent


def band_mention(handle: str) -> str:
    """Render a configured Band handle as a visible @mention.

    Handles should be stored in env/config without a leading @, but Band message
    content needs the visible @ token so the mention can resolve cleanly.
    """

    return f"@{str(handle).strip().removeprefix('@')}"


ROLE_SCENARIO_DETAIL_BANK = {
    "WL-INC-001": {
        "triage": [
            (
                "High-severity Suspicious PowerShell Activity and Possible Data "
                "Exfiltration triage on FIN-042 for j.morgan: powershell.exe "
                "launched invoice_update.exe and "
                "finance_q4_forecast.xlsx access needs Threat Intel and Forensics review."
            ),
            (
                "Route failed logins and outbound 185.199.108.153 context for "
                "parallel indicator and timeline review; exfiltration remains unconfirmed."
            ),
        ],
        "threat_intel": [
            (
                "Indicator context: invoice_update.exe, failed logins, and outbound "
                "185.199.108.153 after powershell.exe activity are suspicious by "
                "scenario evidence; exfiltration remains unconfirmed."
            ),
            (
                "Treat FIN-042 PowerShell indicators as context-risk signals for "
                "Finance governance review, not proof of confirmed compromise."
            ),
        ],
        "forensics": [
            (
                "Evidence timeline links j.morgan on FIN-042, powershell.exe, "
                "invoice_update.exe, finance_q4_forecast.xlsx access, failed "
                "logins, and outbound 185.199.108.153 traffic during suspected "
                "finance-data exposure review."
            ),
            (
                "Preserve endpoint, authentication, file-access, and proxy logs "
                "before validating whether finance_q4_forecast.xlsx exposure occurred."
            ),
        ],
        "compliance": [
            (
                "Finance data exposure risk for FIN-042 and j.morgan requires "
                "evidence retention, management escalation, and review of "
                "finance_q4_forecast.xlsx access; this is not legal advice."
            ),
            (
                "Retain PowerShell, failed-login, file-access, and outbound "
                "185.199.108.153 evidence while scope is validated."
            ),
        ],
        "commander": [
            (
                "Commander decision: contain FIN-042, protect j.morgan credentials, "
                "preserve powershell.exe, invoice_update.exe, finance_q4_forecast.xlsx, "
                "and 185.199.108.153 evidence, and validate scope before external claims."
            ),
            (
                "No downstream handoff; continue containment and evidence preservation "
                "while exfiltration remains unconfirmed."
            ),
        ],
    },
    "WL-INC-002": {
        "triage": [
            (
                "High-severity Credential Stuffing and Impossible Travel triage on "
                "IDP-EDGE-01 for s.patel in Finance: 148 failed logins, repeated "
                "denied MFA pushes, and one successful session need parallel review."
            ),
            (
                "Route 203.0.113.77 and Singapore to Chicago within 11 minutes "
                "travel context to Threat Intel and Forensics."
            ),
        ],
        "threat_intel": [
            (
                "Indicator context: 148 failed logins from 203.0.113.77 plus "
                "Singapore to Chicago within 11 minutes indicate identity-abuse "
                "risk, not confirmed compromise."
            ),
            (
                "Repeated denied MFA pushes followed by one successful session "
                "suggest MFA-fatigue pressure requiring Finance access review."
            ),
        ],
        "forensics": [
            (
                "Evidence timeline links s.patel, 148 failed logins, repeated "
                "denied MFA pushes, one successful session, and impossible travel "
                "on IDP-EDGE-01."
            ),
            (
                "Preserve identity logs, MFA prompt records, session metadata, "
                "and 203.0.113.77 source activity for scope validation."
            ),
        ],
        "compliance": [
            (
                "Finance identity exposure risk for s.patel requires evidence "
                "retention, access review, MFA-fatigue escalation, and management "
                "notification; this is not legal advice."
            ),
            (
                "Review the one successful session after failures before any "
                "external reporting decision."
            ),
        ],
        "commander": [
            (
                "Commander decision: disable s.patel suspicious session, reset "
                "credentials, preserve IDP-EDGE-01, 203.0.113.77, MFA, and "
                "impossible-travel evidence, and validate scope."
            ),
            (
                "No downstream handoff; contain identity access while compromise "
                "remains unconfirmed."
            ),
        ],
    },
    "WL-INC-003": {
        "triage": [
            (
                "High-severity Vendor Invoice Fraud / Business Email Compromise "
                "triage on MAIL-SEC-02 for a.lee in Accounts Payable: "
                "vend0r-payments.example, urgent_wire_invoice_4431.pdf, and "
                "forwarding behavior need parallel review."
            ),
            (
                "Route the $184,500 payment request and auto-forward external "
                "mailbox rule to Threat Intel and Forensics."
            ),
        ],
        "threat_intel": [
            (
                "Indicator context: vend0r-payments.example, urgent_wire_invoice_4431.pdf, "
                "$184,500 urgency, and the mailbox rule indicate invoice-fraud "
                "risk requiring out-of-band validation before payment action."
            ),
            (
                "The lookalike sender domain is suspicious by scenario context, "
                "but payment fraud is not independently confirmed."
            ),
        ],
        "forensics": [
            (
                "Evidence timeline links a.lee, MAIL-SEC-02, vend0r-payments.example, "
                "urgent_wire_invoice_4431.pdf, $184,500, and the auto-forward "
                "external mailbox rule activity for payment-change validation."
            ),
            (
                "Preserve mailbox, message trace, invoice attachment, and forwarding "
                "rule evidence before validating payment-change scope."
            ),
        ],
        "compliance": [
            (
                "Accounts Payable invoice-fraud risk involving a.lee requires "
                "mailbox preservation, payment-change escalation, and management "
                "review; this is not legal advice."
            ),
            (
                "Retain vend0r-payments.example, urgent_wire_invoice_4431.pdf, "
                "$184,500, and forwarding-rule evidence for audit review."
            ),
        ],
        "commander": [
            (
                "Commander decision: preserve a.lee mailbox evidence, disable "
                "the forwarding rule, verify the $184,500 payment change out-of-band, "
                "and validate scope."
            ),
            (
                "No downstream handoff; treat the BEC scenario as suspected until "
                "payment and mailbox evidence are validated."
            ),
        ],
    },
    "WL-INC-004": {
        "triage": [
            (
                "High-severity Cloud Storage Exposure / Public Bucket triage on "
                "CLOUD-STORAGE-01 for svc-data-export in Data Operations: "
                "customer-export-archive has anonymous read enabled for "
                "exports/q4/customer_contacts_q4.csv."
            ),
            (
                "Route anonymous download burst activity against customer-export-archive "
                "to Threat Intel and Forensics for exposure validation."
            ),
        ],
        "threat_intel": [
            (
                "Indicator context: anonymous read enabled plus anonymous download "
                "burst against customer-export-archive suggest public exposure "
                "risk for exports/q4/customer_contacts_q4.csv during exposure validation."
            ),
            (
                "Public ACL and anonymous access patterns are suspicious by "
                "scenario evidence, not proof of confirmed data theft."
            ),
        ],
        "forensics": [
            (
                "Evidence timeline links svc-data-export, anonymous read enabled, "
                "exports/q4/customer_contacts_q4.csv, customer-export-archive, "
                "and anonymous download burst activity for exposure timeline validation."
            ),
            (
                "Preserve cloud access logs, object metadata, ACL history, and "
                "Data Operations service-account evidence before validating exposure."
            ),
        ],
        "compliance": [
            (
                "Data Operations customer export exposure for customer-export-archive "
                "requires evidence retention, access review, public ACL removal, "
                "and management escalation; this is not legal advice."
            ),
            (
                "Retain exports/q4/customer_contacts_q4.csv, ACL history, and "
                "anonymous download burst evidence while scope is validated."
            ),
        ],
        "commander": [
            (
                "Commander decision: revoke anonymous read on customer-export-archive, "
                "protect svc-data-export, preserve exports/q4/customer_contacts_q4.csv "
                "and download evidence, and validate exposure scope."
            ),
            (
                "No downstream handoff; continue containment and evidence preservation "
                "while public exposure scope is validated."
            ),
        ],
    },
    "WL-INC-005": {
        "triage": [
            (
                "High-severity Malware Beacon / Suspicious DNS triage on ENG-117 "
                "for r.kim in Engineering: updater_service.exe calls "
                "cdn-update-check.example every 60 seconds with scheduled task created."
            ),
            (
                "Route repeated lookups every 60 seconds and outbound 198.51.100.42 "
                "activity to Threat Intel and Forensics."
            ),
        ],
        "threat_intel": [
            (
                "Indicator context: updater_service.exe using cdn-update-check.example, "
                "repeated lookups every 60 seconds, and 198.51.100.42 suggests "
                "beacon-like behavior; malware remains unconfirmed."
            ),
            (
                "Scheduled task created plus periodic DNS is suspicious by scenario "
                "evidence, not proof of confirmed compromise."
            ),
        ],
        "forensics": [
            (
                "Evidence timeline links updater_service.exe on ENG-117, repeated "
                "lookups every 60 seconds to cdn-update-check.example, 198.51.100.42, "
                "and scheduled task created."
            ),
            (
                "Preserve DNS telemetry, process lineage, scheduled task artifacts, "
                "and Engineering workstation evidence before validating persistence."
            ),
        ],
        "compliance": [
            (
                "Engineering workstation risk involving updater_service.exe and "
                "cdn-update-check.example requires evidence retention, containment "
                "review, and management escalation; this is not legal advice."
            ),
            (
                "Retain DNS, process, outbound 198.51.100.42, and scheduled task "
                "evidence while scope is validated."
            ),
        ],
        "commander": [
            (
                "Commander decision: isolate ENG-117, protect r.kim, preserve "
                "updater_service.exe, cdn-update-check.example, 198.51.100.42, "
                "and scheduled task evidence, and validate scope during investigation."
            ),
            (
                "No downstream handoff; continue containment while malware and "
                "persistence remain unconfirmed."
            ),
        ],
    },
}


def role_scenario_details(incident_id: str, role: str) -> tuple[str, ...]:
    return tuple(ROLE_SCENARIO_DETAIL_BANK.get(incident_id, {}).get(role, ()))


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
        summary=_triage_summary(incident),
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
        summary=_threat_intel_summary(incident),
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
        summary=_forensics_summary(incident),
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
        summary=_compliance_summary(incident),
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
        summary=_commander_summary(incident),
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


def _triage_summary(incident: IncidentState) -> str:
    banked_summary = _scenario_role_summary(incident, "triage")
    if banked_summary:
        return banked_summary

    return (
        f"High-severity {incident.title} on {incident.affected_host} for "
        f"{incident.affected_user} in {incident.department}; {incident.summary} "
        f"Route Threat Intel and Forensics around {_triage_focus(incident)}."
    )


def _threat_intel_summary(incident: IncidentState) -> str:
    banked_summary = _scenario_role_summary(incident, "threat_intel")
    if banked_summary:
        return banked_summary

    bucket = _indicator_value(incident, "bucket")
    public_acl = _indicator_value(incident, "public_acl")
    access_pattern = _indicator_value(incident, "access_pattern")
    if bucket and public_acl and access_pattern:
        return (
            f"Indicator context: {public_acl} plus {access_pattern} against "
            f"{bucket} suggest public exposure risk for {_object_path(incident)}."
        )

    process = _indicator_value(incident, "process")
    domain = _indicator_value(incident, "domain")
    dns_rate = _indicator_value(incident, "dns_rate")
    destination_ip = _indicator_value(incident, "destination_ip")
    if process and domain and dns_rate:
        return (
            f"Indicator context: {process} using {domain}, {dns_rate}, and "
            f"{destination_ip or 'the supplied destination'} suggests beacon-like "
            "behavior; malware remains unconfirmed."
        )

    failed_count = _indicator_value(incident, "failed_login_count")
    source_ip = _indicator_value(incident, "source_ip")
    impossible_travel = _indicator_value(incident, "impossible_travel")
    if failed_count and source_ip:
        return (
            f"Indicator context: {failed_count} failed logins from {source_ip} "
            f"plus {impossible_travel or 'impossible travel'} indicate identity "
            "abuse risk, not confirmed compromise."
        )

    sender_domain = _indicator_value(incident, "sender_domain")
    invoice_file = _indicator_value(incident, "invoice_file")
    mailbox_rule = _indicator_value(incident, "mailbox_rule")
    if sender_domain and invoice_file:
        return (
            f"Indicator context: {sender_domain}, {invoice_file}, and "
            f"{mailbox_rule or 'mailbox forwarding'} indicate invoice-fraud risk "
            "requiring out-of-band validation."
        )

    primary_indicator = _primary_indicator(incident)
    secondary_indicator = _secondary_indicator(incident)
    return (
        f"Indicator context: {primary_indicator} plus {secondary_indicator} are "
        "suspicious by supplied scenario evidence, with maliciousness unconfirmed."
    )


def _forensics_summary(incident: IncidentState) -> str:
    banked_summary = _scenario_role_summary(incident, "forensics")
    if banked_summary:
        return banked_summary

    bucket = _indicator_value(incident, "bucket")
    public_acl = _indicator_value(incident, "public_acl")
    access_pattern = _indicator_value(incident, "access_pattern")
    if bucket and public_acl and access_pattern:
        return (
            f"Evidence timeline links {incident.affected_user}, {public_acl}, "
            f"{_object_path(incident)}, and {access_pattern} on "
            f"{incident.affected_host}."
        )

    process = _indicator_value(incident, "process")
    domain = _indicator_value(incident, "domain")
    dns_rate = _indicator_value(incident, "dns_rate")
    destination_ip = _indicator_value(incident, "destination_ip")
    persistence = _indicator_value(incident, "persistence")
    if process and domain and dns_rate:
        return (
            f"Evidence timeline links {process} on {incident.affected_host}, "
            f"{dns_rate} to {domain}, {destination_ip or 'outbound traffic'}, and "
            f"{persistence or 'persistence activity'}."
        )

    failed_count = _indicator_value(incident, "failed_login_count")
    source_ip = _indicator_value(incident, "source_ip")
    mfa_pushes = _indicator_value(incident, "mfa_pushes")
    if failed_count and source_ip:
        return (
            f"Evidence timeline links {incident.affected_user}, {failed_count} "
            f"failed logins from {source_ip}, {mfa_pushes or 'MFA prompts'}, and "
            f"{_indicator_value(incident, 'successful_login') or 'session review'}."
        )

    sender_domain = _indicator_value(incident, "sender_domain")
    invoice_file = _indicator_value(incident, "invoice_file")
    mailbox_rule = _indicator_value(incident, "mailbox_rule")
    if sender_domain and invoice_file:
        return (
            f"Evidence timeline links {incident.affected_user}, {sender_domain}, "
            f"{invoice_file}, and {mailbox_rule or 'mailbox forwarding behavior'} "
            f"on {incident.affected_host}."
        )

    return (
        f"Evidence timeline links {incident.affected_host}, "
        f"{incident.affected_user}, {_file_observable(incident)}, and "
        f"{_network_observable(incident)}."
    )


def _compliance_summary(incident: IncidentState) -> str:
    banked_summary = _scenario_role_summary(incident, "compliance")
    if banked_summary:
        return banked_summary

    bucket = _indicator_value(incident, "bucket")
    if bucket:
        return (
            f"{incident.department} customer export exposure for {bucket} requires "
            "evidence retention, access review, public ACL removal, and management "
            "escalation while scope is validated."
        )

    process = _indicator_value(incident, "process")
    domain = _indicator_value(incident, "domain")
    if process and domain:
        return (
            f"{incident.department} workstation activity involving {process} and "
            f"{domain} requires evidence retention, containment review, and "
            "management escalation while scope is validated."
        )

    sender_domain = _indicator_value(incident, "sender_domain")
    mailbox_rule = _indicator_value(incident, "mailbox_rule")
    if sender_domain:
        return (
            f"{incident.department} invoice-fraud risk involving {sender_domain} "
            f"and {mailbox_rule or 'mailbox changes'} requires evidence retention "
            "and payment-change escalation."
        )

    failed_count = _indicator_value(incident, "failed_login_count")
    if failed_count:
        return (
            f"{incident.department} identity activity with {failed_count} failed "
            "logins requires evidence retention, access review, and management "
            "escalation while scope is validated."
        )

    return (
        f"{incident.department} activity involving {incident.affected_user} on "
        f"{incident.affected_host} requires evidence retention and management "
        "escalation while scope is validated."
    )


def _commander_summary(incident: IncidentState) -> str:
    banked_summary = _scenario_role_summary(incident, "commander")
    if banked_summary:
        return banked_summary

    bucket = _indicator_value(incident, "bucket")
    if bucket:
        return (
            f"Commander decision: contain {bucket} on {incident.affected_host}, "
            f"protect {incident.affected_user} credentials, preserve "
            f"{_object_path(incident)} evidence, and validate exposure scope."
        )

    process = _indicator_value(incident, "process")
    domain = _indicator_value(incident, "domain")
    if process and domain:
        return (
            f"Commander decision: contain {incident.affected_host}, protect "
            f"{incident.affected_user}, preserve {process}/{domain} telemetry, "
            "and validate beaconing scope."
        )

    return (
        f"Commander decision: treat {incident.incident_id} as high severity for "
        f"{incident.title} on {incident.affected_host}; contain affected surface, "
        "protect credentials, and validate scope."
    )


def _scenario_role_summary(incident: IncidentState, role: str) -> str | None:
    details = role_scenario_details(incident.incident_id, role)
    return details[0] if details else None


def _triage_focus(incident: IncidentState) -> str:
    bucket = _indicator_value(incident, "bucket")
    public_acl = _indicator_value(incident, "public_acl")
    if bucket and public_acl:
        return f"{bucket} with {public_acl} for {_object_path(incident)}"

    process = _indicator_value(incident, "process")
    domain = _indicator_value(incident, "domain")
    dns_rate = _indicator_value(incident, "dns_rate")
    if process and domain and dns_rate:
        return f"{process}, {domain}, and {dns_rate}"

    failed_count = _indicator_value(incident, "failed_login_count")
    source_ip = _indicator_value(incident, "source_ip")
    if failed_count and source_ip:
        return f"{failed_count} failed logins from {source_ip}"

    sender_domain = _indicator_value(incident, "sender_domain")
    invoice_file = _indicator_value(incident, "invoice_file")
    if sender_domain and invoice_file:
        return f"{sender_domain} and {invoice_file}"

    return _indicator_sentence(incident)


def _object_path(incident: IncidentState) -> str:
    exposed_file = _indicator_value(incident, "exposed_file")
    object_prefix = _indicator_value(incident, "object_prefix")
    if exposed_file and object_prefix:
        return f"{object_prefix.rstrip('/')}/{exposed_file}"
    return exposed_file or object_prefix or _file_observable(incident)


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
