from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock

from app.models.incident import AgentFinding, FinalReport, IncidentState


DEMO_INCIDENT_ID = "WL-INC-001"


SCENARIO_REGISTRY: dict[str, dict[str, object]] = {
    DEMO_INCIDENT_ID: {
        "title": "Suspicious PowerShell Activity and Possible Data Exfiltration",
        "affected_host": "FIN-042",
        "affected_user": "j.morgan",
        "department": "Finance",
        "summary": (
            "Suspicious PowerShell execution on a finance workstation, followed by "
            "failed login attempts, outbound traffic, and sensitive file access."
        ),
        "indicators": {
            "process": "powershell.exe",
            "file": "invoice_update.exe",
            "destination_ip": "185.199.108.153",
            "target_file": "finance_q4_forecast.xlsx",
        },
    },
    "WL-INC-002": {
        "title": "Credential Stuffing and Impossible Travel",
        "affected_host": "IDP-EDGE-01",
        "affected_user": "s.patel",
        "department": "Finance",
        "summary": (
            "High-volume failed login attempts and impossible-travel "
            "authentication activity, including repeated denied MFA prompts and "
            "one successful session after failures."
        ),
        "indicators": {
            "failed_login_count": "148",
            "source_ip": "203.0.113.77",
            "impossible_travel": "Singapore to Chicago within 11 minutes",
            "mfa_pushes": "repeated denied MFA prompts",
            "successful_login": "one successful session after failures",
        },
    },
    "WL-INC-003": {
        "title": "Vendor Invoice Fraud / Business Email Compromise",
        "affected_host": "MAIL-SEC-02",
        "affected_user": "a.lee",
        "department": "Accounts Payable",
        "summary": (
            "Suspected vendor invoice fraud using a lookalike sender domain, "
            "urgent payment request, and mailbox forwarding behavior."
        ),
        "indicators": {
            "sender_domain": "vend0r-payments.example",
            "lookalike_domain": "true",
            "invoice_file": "urgent_wire_invoice_4431.pdf",
            "payment_amount": "184500",
            "mailbox_rule": "auto-forward external mailbox rule",
        },
    },
    "WL-INC-004": {
        "title": "Cloud Storage Exposure / Public Bucket",
        "affected_host": "CLOUD-STORAGE-01",
        "affected_user": "svc-data-export",
        "department": "Data Operations",
        "summary": (
            "Cloud storage exposure involving public anonymous access to an "
            "export archive containing customer contact data."
        ),
        "indicators": {
            "bucket": "customer-export-archive",
            "public_acl": "anonymous read enabled",
            "object_prefix": "exports/q4/",
            "exposed_file": "customer_contacts_q4.csv",
            "access_pattern": "anonymous download burst",
        },
    },
    "WL-INC-005": {
        "title": "Malware Beacon / Suspicious DNS",
        "affected_host": "ENG-117",
        "affected_user": "r.kim",
        "department": "Engineering",
        "summary": (
            "Suspicious periodic DNS and outbound beacon-like behavior from an "
            "engineering workstation with a newly created persistence mechanism."
        ),
        "indicators": {
            "process": "updater_service.exe",
            "domain": "cdn-update-check.example",
            "dns_rate": "repeated lookups every 60 seconds",
            "destination_ip": "198.51.100.42",
            "persistence": "scheduled task created",
        },
    },
}

SUPPORTED_INCIDENT_IDS = tuple(SCENARIO_REGISTRY)


def build_incident(incident_id: str) -> IncidentState:
    normalized_id = incident_id.strip().upper()
    scenario = SCENARIO_REGISTRY.get(normalized_id)
    if scenario is None:
        raise ValueError(f"Unsupported incident ID: {incident_id}")

    return IncidentState(
        incident_id=normalized_id,
        title=str(scenario["title"]),
        status="ready",
        severity="pending",
        affected_host=str(scenario["affected_host"]),
        affected_user=str(scenario["affected_user"]),
        department=str(scenario["department"]),
        summary=str(scenario["summary"]),
        indicators=dict(scenario["indicators"]),
    )


def build_demo_incident() -> IncidentState:
    return build_incident(DEMO_INCIDENT_ID)


class IncidentRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._incidents: dict[str, IncidentState] = {
            incident_id: build_incident(incident_id)
            for incident_id in SUPPORTED_INCIDENT_IDS
        }

    def reset_demo(self) -> IncidentState:
        with self._lock:
            incident = build_demo_incident()
            self._incidents[DEMO_INCIDENT_ID] = incident
            return deepcopy(incident)

    def get(self, incident_id: str) -> IncidentState | None:
        with self._lock:
            incident = self._incidents.get(incident_id)
            return deepcopy(incident) if incident else None

    def upsert(self, incident: IncidentState) -> IncidentState:
        with self._lock:
            incident.updated_at = datetime.now(timezone.utc)
            self._incidents[incident.incident_id] = deepcopy(incident)
            return deepcopy(incident)

    def replace_findings(
        self,
        incident_id: str,
        findings: list[AgentFinding],
        final_report: FinalReport,
    ) -> IncidentState | None:
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident is None:
                return None

            incident.status = "complete"
            incident.severity = final_report.severity
            incident.findings = findings
            incident.final_report = final_report
            incident.updated_at = datetime.now(timezone.utc)
            self._incidents[incident_id] = deepcopy(incident)
            return deepcopy(incident)


incident_repository = IncidentRepository()

