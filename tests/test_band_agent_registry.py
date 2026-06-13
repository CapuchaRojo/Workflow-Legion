import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import Settings  # noqa: E402
from app.services.band_agent_registry import build_band_remote_agent_registry  # noqa: E402


class BandAgentRegistryTests(unittest.TestCase):
    def test_band_remote_agent_registry_maps_all_five_roles(self) -> None:
        settings = Settings(
            band_api_key="legacy-key",
            band_agent_id="legacy-agent-id",
            band_triage_handle="demo/workflow-triage-remote-a",
            band_triage_agent_api_key="triage-key",
            band_triage_agent_id="triage-agent-id",
            band_threat_intel_handle="demo/workflow-threat-intel-ag",
            band_threat_intel_agent_api_key="threat-key",
            band_threat_intel_agent_id="threat-agent-id",
            band_forensics_handle="demo/forensics-agent",
            band_forensics_agent_api_key="forensics-key",
            band_forensics_agent_id="forensics-agent-id",
            band_compliance_handle="demo/compliance-agent",
            band_compliance_agent_api_key="compliance-key",
            band_compliance_agent_id="compliance-agent-id",
            band_commander_handle="demo/commander-agent",
            band_commander_agent_api_key="commander-key",
            band_commander_agent_id="commander-agent-id",
        )

        registry = build_band_remote_agent_registry(settings)

        self.assertEqual(
            sorted(registry),
            [
                "commander",
                "compliance",
                "forensics",
                "threat_intel",
                "triage",
            ],
        )

        self.assertEqual(registry["triage"].handle, "demo/workflow-triage-remote-a")
        self.assertEqual(
            registry["threat_intel"].handle,
            "demo/workflow-threat-intel-ag",
        )
        self.assertEqual(registry["forensics"].handle, "demo/forensics-agent")
        self.assertEqual(registry["compliance"].handle, "demo/compliance-agent")
        self.assertEqual(registry["commander"].handle, "demo/commander-agent")

        self.assertEqual(registry["triage"].agent_api_key, "triage-key")
        self.assertEqual(registry["threat_intel"].agent_api_key, "threat-key")
        self.assertEqual(registry["commander"].agent_id, "commander-agent-id")

    def test_triage_registry_uses_legacy_aliases_when_role_values_missing(
        self,
    ) -> None:
        settings = Settings(
            band_api_key="legacy-key",
            band_agent_id="legacy-agent-id",
            band_triage_handle="@Triage",
            band_triage_agent_api_key=None,
            band_triage_agent_id=None,
        )

        registry = build_band_remote_agent_registry(settings)

        self.assertEqual(registry["triage"].agent_api_key, "legacy-key")
        self.assertEqual(registry["triage"].agent_id, "legacy-agent-id")
        self.assertEqual(registry["triage"].handle, "triage")


if __name__ == "__main__":
    unittest.main()
