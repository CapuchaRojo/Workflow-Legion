import asyncio
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import Settings  # noqa: E402
from app.services.autonomous_band_runtime import build_runtime_from_settings  # noqa: E402
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
                self.assertIn(incident.summary, triage_output.summary)

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
