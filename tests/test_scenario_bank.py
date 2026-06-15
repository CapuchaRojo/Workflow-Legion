import asyncio
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import Settings  # noqa: E402
from app.services.autonomous_role_agents import ROLE_LANGUAGE  # noqa: E402
from app.services.autonomous_band_runtime import build_runtime_from_settings  # noqa: E402
from app.services.deterministic_agents import (  # noqa: E402
    ROLE_SCENARIO_DETAIL_BANK,
    build_commander_finding,
    build_forensics_finding,
)
from app.services.incident_repository import (  # noqa: E402
    DEMO_INCIDENT_ID,
    SCENARIO_REGISTRY,
    SUPPORTED_INCIDENT_IDS,
    build_demo_incident,
    build_incident,
    incident_repository,
)


EXPECTED_SCENARIOS = {
    "WL-INC-001": {
        "title": "Suspicious PowerShell Activity and Possible Data Exfiltration",
        "affected_host": "FIN-042",
        "affected_user": "j.morgan",
        "department": "Finance",
    },
    "WL-INC-002": {
        "title": "Credential Stuffing and Impossible Travel",
        "affected_host": "IDP-EDGE-01",
        "affected_user": "s.patel",
        "department": "Finance",
    },
    "WL-INC-003": {
        "title": "Vendor Invoice Fraud / Business Email Compromise",
        "affected_host": "MAIL-SEC-02",
        "affected_user": "a.lee",
        "department": "Accounts Payable",
    },
    "WL-INC-004": {
        "title": "Cloud Storage Exposure / Public Bucket",
        "affected_host": "CLOUD-STORAGE-01",
        "affected_user": "svc-data-export",
        "department": "Data Operations",
    },
    "WL-INC-005": {
        "title": "Malware Beacon / Suspicious DNS",
        "affected_host": "ENG-117",
        "affected_user": "r.kim",
        "department": "Engineering",
    },
}

WL_INC_001_ONLY_VALUES = (
    "FIN-042",
    "j.morgan",
    "powershell.exe",
    "invoice_update.exe",
    "finance_q4_forecast.xlsx",
    "185.199.108.153",
)

EXPECTED_FORENSICS_CATEGORIES = {
    "WL-INC-001": "process",
    "WL-INC-002": "authentication",
    "WL-INC-003": "mailbox",
    "WL-INC-004": "storage",
    "WL-INC-005": "process",
}

EXPECTED_SCENARIO_ACTIONS = {
    "WL-INC-002": {
        "forensics": "Preserve identity logs and MFA fatigue evidence.",
        "commander": "Disable the suspicious s.patel session immediately.",
    },
    "WL-INC-003": {
        "forensics": "Disable the external forwarding rule pending commander decision.",
        "commander": "Verify the payment change request out-of-band before any payment action.",
    },
    "WL-INC-004": {
        "forensics": "Preserve cloud storage access logs for exports/q4/.",
        "commander": "Revoke anonymous read access on customer-export-archive immediately.",
    },
    "WL-INC-005": {
        "forensics": "Disable the suspicious scheduled task persistence mechanism.",
        "commander": "Preserve DNS and process telemetry for updater_service.exe.",
    },
}

EXPECTED_SUMMARY_INDICATORS = {
    "WL-INC-004": (
        "customer-export-archive",
        "anonymous read",
        "customer_contacts_q4.csv",
        "svc-data-export",
        "exports/q4",
        "anonymous download burst",
    ),
    "WL-INC-005": (
        "updater_service.exe",
        "cdn-update-check.example",
        "repeated lookups",
        "198.51.100.42",
        "scheduled task",
    ),
}

EXPECTED_DETAIL_BANK_VALUES = {
    "WL-INC-001": (
        "FIN-042",
        "j.morgan",
        "powershell.exe",
        "invoice_update.exe",
        "finance_q4_forecast.xlsx",
        "failed logins",
        "185.199.108.153",
    ),
    "WL-INC-002": (
        "IDP-EDGE-01",
        "s.patel",
        "Finance",
        "148 failed logins",
        "203.0.113.77",
        "Singapore to Chicago within 11 minutes",
        "repeated denied MFA pushes",
        "one successful session",
    ),
    "WL-INC-003": (
        "MAIL-SEC-02",
        "a.lee",
        "Accounts Payable",
        "vend0r-payments.example",
        "urgent_wire_invoice_4431.pdf",
        "$184,500",
        "auto-forward external mailbox rule",
    ),
    "WL-INC-004": (
        "CLOUD-STORAGE-01",
        "svc-data-export",
        "Data Operations",
        "customer-export-archive",
        "anonymous read enabled",
        "exports/q4/",
        "customer_contacts_q4.csv",
        "anonymous download burst",
    ),
    "WL-INC-005": (
        "ENG-117",
        "r.kim",
        "Engineering",
        "updater_service.exe",
        "cdn-update-check.example",
        "repeated lookups every 60 seconds",
        "198.51.100.42",
        "scheduled task created",
    ),
}


class ScenarioBankTests(unittest.TestCase):
    def test_all_phase_four_scenarios_are_registered(self) -> None:
        self.assertEqual(set(SUPPORTED_INCIDENT_IDS), set(EXPECTED_SCENARIOS))
        self.assertEqual(set(SCENARIO_REGISTRY), set(EXPECTED_SCENARIOS))

    def test_each_registered_scenario_has_required_fields(self) -> None:
        for incident_id in EXPECTED_SCENARIOS:
            with self.subTest(incident_id=incident_id):
                incident = build_incident(incident_id)

                self.assertEqual(incident.incident_id, incident_id)
                self.assertTrue(incident.title)
                self.assertTrue(incident.affected_host)
                self.assertTrue(incident.affected_user)
                self.assertTrue(incident.department)
                self.assertTrue(incident.summary)
                self.assertGreaterEqual(len(incident.indicators), 3)

    def test_build_demo_incident_still_returns_wl_inc_001(self) -> None:
        incident = build_demo_incident()

        self.assertEqual(DEMO_INCIDENT_ID, "WL-INC-001")
        self.assertEqual(incident.incident_id, DEMO_INCIDENT_ID)
        self.assertEqual(incident.title, EXPECTED_SCENARIOS[DEMO_INCIDENT_ID]["title"])

    def test_build_incident_returns_correct_new_scenario_data(self) -> None:
        for incident_id in ("WL-INC-002", "WL-INC-003", "WL-INC-004", "WL-INC-005"):
            with self.subTest(incident_id=incident_id):
                incident = build_incident(incident_id)
                expected = EXPECTED_SCENARIOS[incident_id]

                self.assertEqual(incident.incident_id, incident_id)
                self.assertEqual(incident.title, expected["title"])
                self.assertEqual(incident.affected_host, expected["affected_host"])
                self.assertEqual(incident.affected_user, expected["affected_user"])
                self.assertEqual(incident.department, expected["department"])

    def test_repository_get_supports_all_registered_scenarios(self) -> None:
        for incident_id in EXPECTED_SCENARIOS:
            with self.subTest(incident_id=incident_id):
                incident = incident_repository.get(incident_id)

                self.assertIsNotNone(incident)
                assert incident is not None
                self.assertEqual(incident.incident_id, incident_id)

    def test_unknown_incident_id_returns_none(self) -> None:
        self.assertIsNone(incident_repository.get("WL-INC-999"))

    def test_role_language_covers_scenario_bank_terms(self) -> None:
        for term in (
            "source ip",
            "sender domain",
            "lookalike",
            "bucket",
            "public acl",
            "dns",
            "beacon",
            "indicator",
        ):
            with self.subTest(role="threat_intel", term=term):
                self.assertIn(term, ROLE_LANGUAGE["threat_intel"])

        for term in (
            "identity",
            "authentication",
            "mailbox",
            "storage",
            "dns",
            "persistence",
            "timeline",
            "evidence",
        ):
            with self.subTest(role="forensics", term=term):
                self.assertIn(term, ROLE_LANGUAGE["forensics"])

    def test_forensics_primary_evidence_category_is_scenario_aware(self) -> None:
        for incident_id, expected_category in EXPECTED_FORENSICS_CATEGORIES.items():
            with self.subTest(incident_id=incident_id):
                finding = build_forensics_finding(
                    build_incident(incident_id),
                    compliance_handle="@ComplianceAgent",
                )

                self.assertEqual(finding.evidence[0].category, expected_category)

    def test_role_detail_bank_covers_all_scenarios_and_roles(self) -> None:
        expected_roles = {
            "triage",
            "threat_intel",
            "forensics",
            "compliance",
            "commander",
        }

        self.assertEqual(set(ROLE_SCENARIO_DETAIL_BANK), set(EXPECTED_SCENARIOS))
        for incident_id, required_values in EXPECTED_DETAIL_BANK_VALUES.items():
            with self.subTest(incident_id=incident_id):
                scenario_bank = ROLE_SCENARIO_DETAIL_BANK[incident_id]
                self.assertEqual(set(scenario_bank), expected_roles)

                detail_text = "\n".join(
                    detail
                    for role_details in scenario_bank.values()
                    for detail in role_details
                )
                for value in required_values:
                    self.assertIn(value, detail_text)

                for role, role_details in scenario_bank.items():
                    with self.subTest(incident_id=incident_id, role=role):
                        self.assertGreaterEqual(len(role_details), 2)
                        self.assertTrue(all(detail.strip() for detail in role_details))

    def test_new_scenario_actions_are_scenario_aware(self) -> None:
        for incident_id, expected_actions in EXPECTED_SCENARIO_ACTIONS.items():
            with self.subTest(incident_id=incident_id):
                incident = build_incident(incident_id)
                forensics = build_forensics_finding(
                    incident,
                    compliance_handle="@ComplianceAgent",
                )
                commander = build_commander_finding(incident)

                self.assertIn(
                    expected_actions["forensics"],
                    forensics.recommended_actions,
                )
                self.assertIn(
                    expected_actions["commander"],
                    commander.recommended_actions,
                )

    def test_new_scenarios_complete_deterministic_dry_run(self) -> None:
        expected_roles = [
            "triage",
            "threat_intel",
            "forensics",
            "compliance",
            "commander",
        ]

        for incident_id in ("WL-INC-002", "WL-INC-003", "WL-INC-004", "WL-INC-005"):
            with self.subTest(incident_id=incident_id):
                with tempfile.TemporaryDirectory() as state_dir:
                    runtime = build_runtime_from_settings(
                        dry_run=True,
                        incident_id=incident_id,
                        state_dir=state_dir,
                        run_id=f"scenario-{incident_id.lower()}",
                        settings_obj=self._settings_without_provider_keys(),
                    )

                    state = asyncio.run(runtime.run_until_complete())

                self.assertEqual(state.status, "complete")
                self.assertEqual(state.completed_roles, expected_roles)
                self.assertEqual(set(state.role_outputs), set(expected_roles))
                self.assertEqual(state.role_outputs["commander"].handoff_roles, [])

                incident = build_incident(incident_id)
                triage_output = state.role_outputs["triage"]
                self.assertIn(incident.title, triage_output.summary)
                self.assertIn(incident.affected_host, triage_output.summary)
                self.assertIn(incident.affected_user, triage_output.summary)
                self.assertIn(incident.department, triage_output.summary)

    def test_triage_threat_intel_forensics_summaries_are_distinct(self) -> None:
        summary_roles = ("triage", "threat_intel", "forensics")

        for incident_id in EXPECTED_SCENARIOS:
            with self.subTest(incident_id=incident_id):
                with tempfile.TemporaryDirectory() as state_dir:
                    runtime = build_runtime_from_settings(
                        dry_run=True,
                        incident_id=incident_id,
                        state_dir=state_dir,
                        run_id=f"distinct-summary-{incident_id.lower()}",
                        settings_obj=self._settings_without_provider_keys(),
                    )

                    state = asyncio.run(runtime.run_until_complete())

                summaries = [
                    state.role_outputs[role].summary
                    for role in summary_roles
                ]

                self.assertEqual(len(set(summaries)), len(summary_roles))
                self.assertEqual(state.role_outputs["commander"].handoff_roles, [])

    def test_storage_and_dns_role_summaries_preserve_scenario_detail(self) -> None:
        summary_roles = ("triage", "threat_intel", "forensics")

        for incident_id, expected_indicators in EXPECTED_SUMMARY_INDICATORS.items():
            with self.subTest(incident_id=incident_id):
                with tempfile.TemporaryDirectory() as state_dir:
                    runtime = build_runtime_from_settings(
                        dry_run=True,
                        incident_id=incident_id,
                        state_dir=state_dir,
                        run_id=f"summary-detail-{incident_id.lower()}",
                        settings_obj=self._settings_without_provider_keys(),
                    )

                    state = asyncio.run(runtime.run_until_complete())

                summaries = [
                    state.role_outputs[role].summary
                    for role in summary_roles
                ]
                summary_text = "\n".join(summaries)

                self.assertEqual(len(set(summaries)), len(summary_roles))
                for indicator in expected_indicators:
                    with self.subTest(incident_id=incident_id, indicator=indicator):
                        self.assertIn(indicator, summary_text)

    def test_role_summaries_do_not_leak_unrelated_scenario_indicators(self) -> None:
        summary_roles = ("triage", "threat_intel", "forensics")
        indicator_values_by_incident = {
            incident_id: {
                value
                for value in SCENARIO_REGISTRY[incident_id]["indicators"].values()
                if len(str(value)) > 3
            }
            for incident_id in EXPECTED_SCENARIOS
        }

        for incident_id in EXPECTED_SCENARIOS:
            with self.subTest(incident_id=incident_id):
                with tempfile.TemporaryDirectory() as state_dir:
                    runtime = build_runtime_from_settings(
                        dry_run=True,
                        incident_id=incident_id,
                        state_dir=state_dir,
                        run_id=f"summary-leakage-{incident_id.lower()}",
                        settings_obj=self._settings_without_provider_keys(),
                    )

                    state = asyncio.run(runtime.run_until_complete())

                summary_text = "\n".join(
                    state.role_outputs[role].summary
                    for role in summary_roles
                )
                current_values = indicator_values_by_incident[incident_id]

                for other_incident_id, other_values in indicator_values_by_incident.items():
                    if other_incident_id == incident_id:
                        continue
                    for value in other_values - current_values:
                        self.assertNotIn(str(value), summary_text)

    def test_new_scenario_dry_runs_do_not_leak_wl_inc_001_indicators(self) -> None:
        for incident_id in ("WL-INC-002", "WL-INC-003", "WL-INC-004", "WL-INC-005"):
            with self.subTest(incident_id=incident_id):
                with tempfile.TemporaryDirectory() as state_dir:
                    runtime = build_runtime_from_settings(
                        dry_run=True,
                        incident_id=incident_id,
                        state_dir=state_dir,
                        run_id=f"leakage-{incident_id.lower()}",
                        settings_obj=self._settings_without_provider_keys(),
                    )

                    state = asyncio.run(runtime.run_until_complete())

                incident = build_incident(incident_id)
                scenario_values = {
                    incident.incident_id,
                    incident.title,
                    incident.affected_host,
                    incident.affected_user,
                    incident.department,
                    incident.summary,
                    *incident.indicators.values(),
                }
                output_text = "\n".join(
                    "\n".join(
                        (
                            output.summary,
                            *output.evidence,
                            *output.recommended_actions,
                            output.band_message,
                        )
                    )
                    for output in state.role_outputs.values()
                )

                for wl_inc_001_value in WL_INC_001_ONLY_VALUES:
                    if wl_inc_001_value in scenario_values:
                        continue
                    self.assertNotIn(wl_inc_001_value, output_text)

    def _settings_without_provider_keys(self) -> Settings:
        return Settings(
            band_api_key=None,
            band_agent_id=None,
            band_chat_id=None,
            band_room_id=None,
            band_triage_agent_id=None,
            band_threat_intel_agent_id=None,
            band_forensics_agent_id=None,
            band_compliance_agent_id=None,
            band_commander_agent_id=None,
            band_triage_agent_api_key=None,
            band_threat_intel_agent_api_key=None,
            band_forensics_agent_api_key=None,
            band_compliance_agent_api_key=None,
            band_commander_agent_api_key=None,
            band_triage_handle="redhood/workflow-triage-remote-a",
            band_threat_intel_handle="redhood/workflow-threat-intel-ag",
            band_forensics_handle="redhood/workflow-forensics-agent",
            band_compliance_handle="redhood/workflow-compliance-agent",
            band_commander_handle="redhood/workflow-incident-commander",
            aiml_api_key=None,
            aiml_model=None,
            aimlapi_api_key=None,
            aimlapi_model=None,
            featherless_api_key=None,
            featherless_model=None,
            autonomous_agent_provider_mode="deterministic",
        )


if __name__ == "__main__":
    unittest.main()
