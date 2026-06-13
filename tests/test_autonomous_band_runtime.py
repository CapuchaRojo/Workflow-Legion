import asyncio
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import Settings  # noqa: E402
from app.main import StartIncidentRequest, start_demo_incident  # noqa: E402
from app.services.autonomous_agent_state import (  # noqa: E402
    AutonomousRunState,
    AutonomousStateStore,
)
from app.services.autonomous_band_runtime import (  # noqa: E402
    AutonomousBandRuntime,
    BandMessageEvent,
    DryRunBandMessenger,
    LiveBandEventSource,
    ScriptedBandEventSource,
    build_dry_run_start_event,
    build_runtime_from_settings,
    parse_auto_start,
    parse_run_marker,
)
import run_autonomous_agents  # noqa: E402
from run_autonomous_agents import parse_args  # noqa: E402
from app.services.autonomous_role_agents import (  # noqa: E402
    ROLE_DEFINITIONS,
    AutonomousReasoningProvider,
    AutonomousRoleContext,
)
from app.services.band_agent_registry import build_band_remote_agent_registry  # noqa: E402
from app.services.incident_repository import build_demo_incident  # noqa: E402


class AutonomousBandRuntimeTests(unittest.TestCase):
    def test_auto_start_parser_accepts_required_prompt(self) -> None:
        self.assertEqual(
            parse_auto_start(
                "@redhood/workflow-triage-remote-a AUTO:START WL-INC-001"
            ),
            "WL-INC-001",
        )
        self.assertIsNone(parse_auto_start("@triage start WL-INC-001"))

    def test_mention_trigger_detection_requires_triage_mention(self) -> None:
        runtime = self._runtime_with_empty_source()
        event = BandMessageEvent(
            message_id="m-no-mention",
            content="AUTO:START WL-INC-001",
            author_handle="human",
        )

        asyncio.run(runtime.handle_event(event))

        self.assertIsNone(runtime.state)

    def test_display_name_mention_starts_triage(self) -> None:
        runtime = self._runtime_with_empty_source()
        event = BandMessageEvent(
            message_id="m-display-start",
            content="@Workflow Triage Remote Agent AUTO:START WL-INC-001",
            author_handle="human",
        )

        asyncio.run(runtime.handle_event(event))

        self.assertIsNotNone(runtime.state)
        self.assertEqual(runtime.state.completed_roles, ["triage"])

    def test_structured_mention_metadata_starts_triage(self) -> None:
        runtime = self._runtime_with_empty_source()
        event = BandMessageEvent(
            message_id="m-structured-start",
            content="AUTO:START WL-INC-001",
            author_handle="human",
            mention_metadata=({"name": "Workflow Triage Remote Agent"},),
        )

        asyncio.run(runtime.handle_event(event))

        self.assertIsNotNone(runtime.state)
        self.assertEqual(runtime.state.completed_roles, ["triage"])

    def test_raw_handle_mention_matching_still_works(self) -> None:
        runtime = self._runtime_with_empty_source()
        triage_handle = runtime.registry["triage"].handle
        event = BandMessageEvent(
            message_id="m-raw-handle",
            content=f"@{triage_handle} AUTO:START WL-INC-001",
            author_handle="human",
        )

        self.assertTrue(runtime._event_mentions_role(event, "triage"))

    def test_role_routing_and_handoff_targets_follow_band_mentions(self) -> None:
        runtime = self._runtime_with_empty_source()
        registry = runtime.registry
        start = build_dry_run_start_event(registry, "WL-INC-001")

        asyncio.run(runtime.handle_event(start))

        self.assertIsNotNone(runtime.state)
        self.assertEqual(runtime.state.completed_roles, ["triage"])
        source = runtime.event_source
        self.assertIsInstance(source, ScriptedBandEventSource)
        triage_message = source.published_events[0]

        self.assertEqual(
            set(runtime._roles_triggered_by_event(triage_message)),
            {"threat_intel", "forensics"},
        )
        marker = parse_run_marker(triage_message.content)
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker["role"], "triage")
        self.assertIn(registry["threat_intel"].handle, triage_message.mention_handles)
        self.assertIn(registry["forensics"].handle, triage_message.mention_handles)

    def test_loop_prevention_ignores_own_authored_start_message(self) -> None:
        runtime = self._runtime_with_empty_source()
        triage_handle = runtime.registry["triage"].handle
        event = BandMessageEvent(
            message_id="m-own-start",
            content=f"@{triage_handle} AUTO:START WL-INC-001",
            author_handle=triage_handle,
            mention_handles=(triage_handle,),
        )

        asyncio.run(runtime.handle_event(event))

        self.assertIsNone(runtime.state)

    def test_loop_prevention_processes_message_once_per_role(self) -> None:
        runtime = self._runtime_with_empty_source(
            state=AutonomousRunState(
                incident_id="WL-INC-001",
                run_id="unit",
            )
        )
        triage_handle = runtime.registry["triage"].handle
        event = BandMessageEvent(
            message_id="m-duplicate",
            content=f"@{triage_handle} AUTO:START WL-INC-001",
            author_handle="human",
            mention_handles=(triage_handle,),
        )

        asyncio.run(runtime.handle_event(event))
        asyncio.run(runtime.handle_event(event))

        self.assertEqual(runtime.state.completed_roles, ["triage"])
        self.assertEqual(runtime.state.processed_message_ids["triage"], ["m-duplicate"])
        messenger = runtime.messenger
        self.assertIsInstance(messenger, DryRunBandMessenger)
        self.assertEqual(len(messenger.sent_messages), 1)

    def test_provider_falls_back_without_credentials(self) -> None:
        provider = AutonomousReasoningProvider(
            provider_mode="auto",
            settings_obj=self._settings_without_provider_keys(),
        )
        registry = build_band_remote_agent_registry(self._settings_without_provider_keys())
        context = AutonomousRoleContext(
            incident=build_demo_incident(),
            run_id="unit",
            source_message_ids=("m1",),
            upstream_summaries={},
            handles_by_role={role: agent.handle for role, agent in registry.items()},
        )

        output = asyncio.run(provider.decide(ROLE_DEFINITIONS["triage"], context))

        self.assertEqual(output.provider_name, "aimlapi")
        self.assertEqual(output.provider_mode, "deterministic_fallback")
        self.assertIn("[WL-AUTO:WL-INC-001:triage:unit]", output.band_message)

    def test_compliance_double_mention_is_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            runtime = build_runtime_from_settings(
                dry_run=True,
                incident_id="WL-INC-001",
                state_dir=state_dir,
                settings_obj=self._settings_without_provider_keys(),
            )

            state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.status, "complete")
        self.assertEqual(state.completed_roles.count("compliance"), 1)
        self.assertEqual(state.turn_count, 5)
        self.assertEqual(len(state.processed_message_ids["compliance"]), 2)
        self.assertEqual(state.role_outputs["compliance"].handoff_roles, ["commander"])

    def test_commander_stop_condition_completes_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            runtime = build_runtime_from_settings(
                dry_run=True,
                incident_id="WL-INC-001",
                state_dir=state_dir,
                settings_obj=self._settings_without_provider_keys(),
            )

            state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.status, "complete")
        self.assertEqual(state.completed_roles[-1], "commander")
        self.assertIsNotNone(state.final_decision_state)
        self.assertEqual(state.role_outputs["commander"].handoff_roles, [])

    def test_dump_recent_messages_does_not_send_agent_replies(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        registry = build_band_remote_agent_registry(settings_obj)
        source = ScriptedBandEventSource(
            [build_dry_run_start_event(registry, "WL-INC-001")]
        )
        messenger = DryRunBandMessenger(registry)
        runtime = AutonomousBandRuntime(
            registry=registry,
            event_source=source,
            messenger=messenger,
            reasoning_provider=AutonomousReasoningProvider(
                provider_mode="deterministic",
                settings_obj=settings_obj,
            ),
            state_store=AutonomousStateStore(tempfile.mkdtemp()),
            settings_obj=settings_obj,
        )

        output = io.StringIO()
        with redirect_stdout(output):
            events = asyncio.run(runtime.dump_recent_messages(message_limit=5))

        self.assertEqual(len(events), 1)
        self.assertEqual(messenger.sent_messages, [])
        self.assertIsNone(runtime.state)
        self.assertIn("matched_roles=triage", output.getvalue())

    def test_dry_run_autonomous_chain_completes(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            runtime = build_runtime_from_settings(
                dry_run=True,
                incident_id="WL-INC-001",
                state_dir=state_dir,
                settings_obj=self._settings_without_provider_keys(),
            )

            state = asyncio.run(runtime.run_until_complete())
            status_path = AutonomousStateStore(state_dir).mission_control_path()
            self.assertTrue(status_path.exists())

        self.assertEqual(
            state.completed_roles,
            ["triage", "threat_intel", "forensics", "compliance", "commander"],
        )

    def test_explicit_run_id_is_propagated_to_all_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            runtime = build_runtime_from_settings(
                dry_run=True,
                incident_id="WL-INC-001",
                state_dir=state_dir,
                run_id="operator-check",
                settings_obj=self._settings_without_provider_keys(),
            )

            state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.run_id, "operator-check")
        for role, output in state.role_outputs.items():
            marker = f"[WL-AUTO:WL-INC-001:{role}:operator-check]"
            self.assertIn(marker, output.band_message)

    def test_stop_after_complete_leaves_post_commander_events_unread(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        registry = build_band_remote_agent_registry(settings_obj)
        source = _SentinelAfterCommanderSource(
            [build_dry_run_start_event(registry, "WL-INC-001")]
        )
        runtime = AutonomousBandRuntime(
            registry=registry,
            event_source=source,
            messenger=DryRunBandMessenger(registry),
            reasoning_provider=AutonomousReasoningProvider(
                provider_mode="deterministic",
                settings_obj=settings_obj,
            ),
            state=AutonomousRunState(
                incident_id="WL-INC-001",
                run_id="stop-check",
            ),
            state_store=AutonomousStateStore(tempfile.mkdtemp()),
            run_id="stop-check",
            stop_after_complete=True,
            settings_obj=settings_obj,
        )

        state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.status, "complete")
        self.assertFalse(source.sentinel_was_read)

    def test_poll_interval_and_safety_cli_flags_parse(self) -> None:
        args = parse_args(
            [
                "--poll-interval",
                "7.5",
                "--run-id",
                "manual-run",
                "--no-stop-after-complete",
                "--once",
                "--debug-receive",
                "--dump-recent-messages",
                "--message-limit",
                "9",
            ]
        )

        self.assertEqual(args.poll_interval, 7.5)
        self.assertEqual(args.run_id, "manual-run")
        self.assertFalse(args.stop_after_complete)
        self.assertTrue(args.single_pass)
        self.assertTrue(args.debug_receive)
        self.assertTrue(args.dump_recent_messages)
        self.assertEqual(args.message_limit, 9)

    def test_live_runtime_receives_poll_interval_and_single_pass(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        settings_obj.band_chat_id = "placeholder-chat-id"
        settings_obj.band_triage_agent_api_key = "placeholder-triage-key"

        runtime = build_runtime_from_settings(
            dry_run=False,
            poll_interval_seconds=6.0,
            single_pass=True,
            message_limit=9,
            settings_obj=settings_obj,
        )

        self.assertIsInstance(runtime.event_source, LiveBandEventSource)
        assert isinstance(runtime.event_source, LiveBandEventSource)
        self.assertEqual(runtime.event_source.poll_interval_seconds, 6.0)
        self.assertTrue(runtime.event_source.single_pass)
        self.assertEqual(runtime.event_source.message_limit, 9)

    def test_cancelled_cli_path_exits_cleanly(self) -> None:
        async def cancelled_main(argv=None):
            raise asyncio.CancelledError()

        output = io.StringIO()
        with patch.object(run_autonomous_agents, "main", cancelled_main):
            with redirect_stdout(output):
                exit_code = run_autonomous_agents.run_cli([])

        self.assertEqual(exit_code, 130)
        self.assertIn(
            "Autonomous runtime stopped by operator.",
            output.getvalue(),
        )

    def test_max_turns_safety_still_stops_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            runtime = build_runtime_from_settings(
                dry_run=True,
                incident_id="WL-INC-001",
                state_dir=state_dir,
                max_turns=1,
                run_id="turn-limit",
                settings_obj=self._settings_without_provider_keys(),
            )

            state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.status, "max_turns_exceeded")
        self.assertEqual(state.completed_roles, ["triage"])

    def test_deterministic_endpoint_still_completes(self) -> None:
        response = asyncio.run(
            start_demo_incident(StartIncidentRequest(reset=True, post_to_band=False))
        )

        self.assertEqual(response.incident.incident_id, "WL-INC-001")
        self.assertEqual(response.incident.status, "complete")
        self.assertEqual(len(response.incident.findings), 5)
        self.assertEqual(response.band_delivery, [])

    def _runtime_with_empty_source(
        self,
        state: AutonomousRunState | None = None,
    ) -> AutonomousBandRuntime:
        settings_obj = self._settings_without_provider_keys()
        registry = build_band_remote_agent_registry(settings_obj)
        source = ScriptedBandEventSource()
        messenger = DryRunBandMessenger(registry)
        return AutonomousBandRuntime(
            registry=registry,
            event_source=source,
            messenger=messenger,
            reasoning_provider=AutonomousReasoningProvider(
                provider_mode="deterministic",
                settings_obj=settings_obj,
            ),
            state=state,
            state_store=AutonomousStateStore(tempfile.mkdtemp()),
            settings_obj=settings_obj,
        )

    def _settings_without_provider_keys(self) -> Settings:
        return Settings(
            band_api_key=None,
            band_agent_id=None,
            band_chat_id=None,
            band_room_id=None,
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


class _SentinelAfterCommanderSource(ScriptedBandEventSource):
    def __init__(self, events: list[BandMessageEvent]) -> None:
        super().__init__(events)
        self.sentinel_was_read = False

    async def events(self):
        while self._events:
            event = self._events.popleft()
            if event.message_id == "sentinel-after-complete":
                self.sentinel_was_read = True
            yield event

    async def publish_sent_message(self, sent_message, author_handle: str) -> None:
        await super().publish_sent_message(sent_message, author_handle)
        if sent_message.role == "commander":
            self._events.append(
                BandMessageEvent(
                    message_id="sentinel-after-complete",
                    content="post-complete diagnostic event",
                    author_handle="human",
                )
            )


if __name__ == "__main__":
    unittest.main()
