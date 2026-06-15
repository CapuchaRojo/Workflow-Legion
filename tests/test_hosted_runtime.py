import json
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.autonomous_agent_state import (  # noqa: E402
    AutonomousRunState,
    build_frontend_mission_control_export,
)
from hosted_runtime import (  # noqa: E402
    HostedRuntimeConfig,
    create_app,
    load_mission_control_status,
    _runtime_argv,
)
from run_autonomous_agents import parse_args  # noqa: E402


class HostedRuntimeTests(unittest.TestCase):
    def test_status_route_returns_sanitized_mission_control_export(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            export_path = Path(state_dir) / "mission-control-status.hosted.json"
            payload = build_frontend_mission_control_export(
                AutonomousRunState(
                    incident_id="WL-INC-001",
                    run_id="hosted-test",
                )
            )
            payload["band_chat_id"] = "chat-value"
            payload["roles"][0]["agent_id"] = "configured-agent-id"
            payload["roles"][0]["delivery"]["authorization"] = "Bearer private"
            payload["roles"][0]["delivery"]["detail"] = "token=private-token"
            export_path.write_text(json.dumps(payload), encoding="utf-8")

            app = create_app(config=self._config(state_dir, export_path))
            client = TestClient(app)

            response = client.get("/mission-control-status")

        self.assertEqual(response.status_code, 200)
        body = response.text
        data = response.json()
        self.assertEqual(data["incident_id"], "WL-INC-001")
        self.assertEqual(data["run_id"], "hosted-test")
        self.assertIn("roles", data)
        self.assertNotIn("band_chat_id", body)
        self.assertNotIn("configured-agent-id", body)
        self.assertNotIn("authorization", body)
        self.assertNotIn("private-token", body)

    def test_status_loader_converts_full_state_to_sanitized_export(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_path = Path(state_dir) / "mission-control-status.json"
            full_state = AutonomousRunState(
                incident_id="WL-INC-001",
                run_id="full-state-test",
            ).to_dict()
            full_state["band_room_id"] = "room-value"
            state_path.write_text(json.dumps(full_state), encoding="utf-8")

            data = load_mission_control_status(
                self._config(
                    state_dir,
                    Path(state_dir) / "missing-hosted-export.json",
                )
            )

        encoded = json.dumps(data)
        self.assertEqual(data["run_id"], "full-state-test")
        self.assertIn("roles", data)
        self.assertNotIn("role_outputs", encoded)
        self.assertNotIn("band_room_id", encoded)
        self.assertNotIn("room-value", encoded)

    def test_health_route_reports_runtime_without_private_config_values(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            app = create_app(
                config=self._config(
                    state_dir,
                    Path(state_dir) / "mission-control-status.hosted.json",
                )
            )
            client = TestClient(app)

            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], "workflow-legion-hosted-runtime")
        self.assertEqual(data["runtime"]["runtime_state"], "disabled")
        self.assertNotIn("band_chat_id", response.text)
        self.assertNotIn("agent_api_key", response.text)

    def test_hosted_runtime_argv_reuses_cli_runtime_options(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            export_path = Path(state_dir) / "mission-control-status.hosted.json"
            args = parse_args(_runtime_argv(self._config(state_dir, export_path)))

        self.assertEqual(args.state_dir, state_dir)
        self.assertEqual(args.frontend_studio_export, str(export_path))
        self.assertEqual(args.message_limit, 25)
        self.assertEqual(args.poll_interval, 5.0)
        self.assertTrue(args.baseline_existing)
        self.assertTrue(args.stop_after_complete)

    def _config(self, state_dir: str, export_path: Path) -> HostedRuntimeConfig:
        return HostedRuntimeConfig(
            autostart=False,
            dry_run=False,
            incident_id="WL-INC-001",
            state_dir=Path(state_dir),
            mission_control_export=export_path,
            max_turns=12,
            poll_interval_seconds=5.0,
            message_limit=25,
            run_id=None,
            stop_after_complete=True,
            baseline_existing_messages=True,
            debug_receive=False,
            restart_after_complete=True,
            restart_delay_seconds=2.0,
        )


if __name__ == "__main__":
    unittest.main()
