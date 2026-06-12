"""Tests for the deterministic five-agent demo path."""

import unittest

from agents import AGENT_IDS, get_mock_agent_output
from agents.contracts import DEMO_INCIDENT_ID


class AgentMockOutputTests(unittest.TestCase):
    def test_all_five_agent_outputs_are_available_and_stable(self) -> None:
        self.assertEqual(
            AGENT_IDS,
            ("triage", "threat_intel", "forensics", "compliance", "commander"),
        )

        for agent_id in AGENT_IDS:
            first = get_mock_agent_output(agent_id)
            second = get_mock_agent_output(agent_id)

            self.assertEqual(first, second)
            self.assertEqual(first.incident_id, DEMO_INCIDENT_ID)
            self.assertEqual(first.agent_id, agent_id)
            self.assertEqual(first.status, "completed")
            self.assertEqual(first.mode, "deterministic_mock")
            self.assertTrue(first.band_message)
            self.assertTrue(first.summary)

    def test_band_handoff_chain_is_explicit(self) -> None:
        triage = get_mock_agent_output("triage")
        threat_intel = get_mock_agent_output("threat-intel")
        forensics = get_mock_agent_output("forensics")
        compliance = get_mock_agent_output("compliance")
        commander = get_mock_agent_output("commander")

        self.assertEqual(triage.handoff_to, ("threat_intel", "forensics"))
        self.assertIn("@ThreatIntelAgent", triage.band_message)
        self.assertIn("@ForensicsAgent", triage.band_message)
        self.assertEqual(threat_intel.handoff_to, ("compliance",))
        self.assertEqual(forensics.handoff_to, ("compliance",))
        self.assertEqual(compliance.handoff_to, ("commander",))
        self.assertEqual(commander.handoff_to, ())

    def test_outputs_are_json_serializable(self) -> None:
        import json

        for agent_id in AGENT_IDS:
            serialized = json.dumps(get_mock_agent_output(agent_id).to_dict())
            self.assertIn(DEMO_INCIDENT_ID, serialized)

    def test_unknown_agent_and_incident_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            get_mock_agent_output("unknown")

        with self.assertRaises(ValueError):
            get_mock_agent_output("triage", "WL-INC-999")


if __name__ == "__main__":
    unittest.main()
