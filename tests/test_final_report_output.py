"""Tests for the deterministic final incident report output."""

import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.deterministic_agents import run_deterministic_workflow  # noqa: E402
from app.services.final_report import build_final_report  # noqa: E402
from app.services.incident_repository import (  # noqa: E402
    DEMO_INCIDENT_ID,
    build_demo_incident,
    incident_repository,
)


class FinalReportOutputTests(unittest.TestCase):
    def test_final_report_contains_required_submission_sections(self) -> None:
        incident = build_demo_incident()
        findings = run_deterministic_workflow(
            incident,
            threat_handle="@ThreatIntelAgent",
            forensics_handle="@ForensicsAgent",
            compliance_handle="@ComplianceAgent",
            commander_handle="@IncidentCommanderAgent",
        )

        report = build_final_report(incident, findings)

        self.assertEqual(report.incident_id, DEMO_INCIDENT_ID)
        self.assertEqual(report.severity, "high")
        self.assertIn("PowerShell", report.executive_summary)
        self.assertIn("FIN-042", report.executive_summary)
        self.assertIn("possible data exposure", report.executive_summary)
        self.assertIn("Contain FIN-042", report.commander_decision)

        self.assertGreaterEqual(len(report.evidence_summary), 5)
        self.assertTrue(
            any("EV-TG-001" in evidence for evidence in report.evidence_summary)
        )
        self.assertTrue(
            any("EV-FO-002" in evidence for evidence in report.evidence_summary)
        )

        self.assertGreaterEqual(len(report.timeline_summary), 4)
        self.assertTrue(
            any("09:14" in event and "PowerShell" in event for event in report.timeline_summary)
        )
        self.assertTrue(
            any("09:22" in event and "185.199.108.153" in event for event in report.timeline_summary)
        )

        self.assertGreaterEqual(len(report.compliance_notes), 3)
        self.assertIn("Open an evidence retention record.", report.compliance_notes)
        self.assertIn(
            "Defer external notification until exfiltration scope is confirmed.",
            report.compliance_notes,
        )

        self.assertIn("Isolate FIN-042 immediately.", report.recommended_actions)
        self.assertIn(
            "Reset j.morgan credentials and revoke active sessions.",
            report.recommended_actions,
        )
        self.assertIn(
            "Preserve endpoint, identity, file, and network evidence.",
            report.recommended_actions,
        )

    def test_final_report_is_stored_on_completed_incident_state(self) -> None:
        incident = incident_repository.reset_demo()
        findings = run_deterministic_workflow(
            incident,
            threat_handle="@ThreatIntelAgent",
            forensics_handle="@ForensicsAgent",
            compliance_handle="@ComplianceAgent",
            commander_handle="@IncidentCommanderAgent",
        )
        report = build_final_report(incident, findings)

        completed_incident = incident_repository.replace_findings(
            incident.incident_id,
            findings,
            report,
        )

        self.assertIsNotNone(completed_incident)
        assert completed_incident is not None

        self.assertEqual(completed_incident.status, "complete")
        self.assertEqual(completed_incident.severity, "high")
        self.assertEqual(len(completed_incident.findings), 5)
        self.assertIsNotNone(completed_incident.final_report)
        self.assertEqual(
            completed_incident.final_report.commander_decision,
            report.commander_decision,
        )


if __name__ == "__main__":
    unittest.main()
