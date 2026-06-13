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
    def test_all_five_backend_findings_are_complete_and_deterministic(self) -> None:
        incident = build_demo_incident()
        handles = {
            "threat_handle": "@ThreatIntelAgent",
            "forensics_handle": "@ForensicsAgent",
            "compliance_handle": "@ComplianceAgent",
            "commander_handle": "@IncidentCommanderAgent",
        }
        findings = run_deterministic_workflow(incident, **handles)
        repeated_findings = run_deterministic_workflow(
            build_demo_incident(),
            **handles,
        )

        self.assertEqual(
            [finding.agent for finding in findings],
            ["triage", "threat_intel", "forensics", "compliance", "commander"],
        )

        for finding in findings:
            with self.subTest(agent=finding.agent):
                self.assertEqual(finding.status, "complete")
                self.assertEqual(finding.severity, "high")
                self.assertIn(finding.confidence, {"medium", "high"})
                self.assertTrue(finding.summary)
                self.assertTrue(finding.recommended_actions)
                self.assertTrue(finding.band_message)

        normalized = [
            finding.model_dump(exclude={"created_at"}) for finding in findings
        ]
        repeated_normalized = [
            finding.model_dump(exclude={"created_at"})
            for finding in repeated_findings
        ]
        self.assertEqual(normalized, repeated_normalized)

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

    def test_final_report_aggregates_all_evidence_and_actions(self) -> None:
        incident = build_demo_incident()
        findings = run_deterministic_workflow(
            incident,
            threat_handle="@ThreatIntelAgent",
            forensics_handle="@ForensicsAgent",
            compliance_handle="@ComplianceAgent",
            commander_handle="@IncidentCommanderAgent",
        )
        report = build_final_report(incident, findings)

        expected_evidence = [
            f"{evidence.evidence_id}: {evidence.summary}"
            for finding in findings
            for evidence in finding.evidence
        ]
        expected_actions = list(
            dict.fromkeys(
                action
                for finding in findings
                for action in finding.recommended_actions
            )
        )
        compliance_finding = next(
            finding
            for finding in findings
            if finding.agent == "compliance"
        )

        self.assertEqual(report.evidence_summary, expected_evidence)
        self.assertEqual(report.recommended_actions, expected_actions)
        self.assertEqual(
            report.compliance_notes,
            compliance_finding.recommended_actions,
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
