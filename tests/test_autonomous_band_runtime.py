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

    def test_band_internal_mention_token_starts_triage_with_configured_agent_id(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        settings_obj.band_triage_agent_id = "fake-triage-agent-id"
        runtime = self._runtime_with_empty_source(settings_obj=settings_obj)
        event = BandMessageEvent(
            message_id="m-internal-token-start",
            content="@[[fake-triage-agent-id]] AUTO:START WL-INC-001",
            author_handle="human",
        )

        asyncio.run(runtime.handle_event(event))

        self.assertIsNotNone(runtime.state)
        self.assertEqual(runtime.state.completed_roles, ["triage"])

    def test_structured_mention_id_matches_configured_agent_id(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        settings_obj.band_triage_agent_id = "fake-triage-agent-id"
        runtime = self._runtime_with_empty_source(settings_obj=settings_obj)
        event = BandMessageEvent(
            message_id="m-structured-id-start",
            content="AUTO:START WL-INC-001",
            author_handle="human",
            mention_metadata=({"id": "fake-triage-agent-id"},),
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

    def test_downstream_agents_react_to_agent_authored_upstream_message(self) -> None:
        runtime = self._runtime_with_empty_source(
            state=AutonomousRunState(
                incident_id="WL-INC-001",
                run_id="unit",
                status="running",
                completed_roles=["triage"],
            )
        )
        registry = runtime.registry
        event = BandMessageEvent(
            message_id="m-triage-output",
            content=(
                f"@{registry['threat_intel'].handle} "
                f"@{registry['forensics'].handle} "
                "[WL-AUTO:WL-INC-001:triage:unit] Triage complete."
            ),
            author_handle=registry["triage"].handle,
            mention_handles=(
                registry["threat_intel"].handle,
                registry["forensics"].handle,
            ),
        )

        asyncio.run(runtime.handle_event(event))

        self.assertIn("threat_intel", runtime.state.completed_roles)
        self.assertIn("forensics", runtime.state.completed_roles)
        messenger = runtime.messenger
        self.assertIsInstance(messenger, DryRunBandMessenger)
        self.assertEqual(len(messenger.sent_messages), 2)

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

    def test_debug_receive_counts_band_internal_mentions_without_configured_ids(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        settings_obj.band_triage_agent_id = "fake-triage-agent-id"
        runtime = self._runtime_with_empty_source(settings_obj=settings_obj)
        event = BandMessageEvent(
            message_id="m-debug-internal-token",
            content="@[[fake-triage-agent-id]] AUTO:START WL-INC-001",
            author_handle="human",
        )

        output = io.StringIO()
        with redirect_stdout(output):
            runtime.print_receive_diagnostics([event])

        diagnostics = output.getvalue()
        self.assertIn("band_internal_mentions_detected=1", diagnostics)
        self.assertIn("matched_any_role=True matched_roles=triage", diagnostics)

    def test_debug_receive_distinguishes_new_and_seen_messages(self) -> None:
        runtime = self._runtime_with_empty_source()
        source = LiveBandEventSource(
            base_url="https://band.example/api",
            chat_id="chat",
            agent_api_key="key",
        )
        source._seen_message_ids.add("m-seen")
        batch = source.build_receive_batch(
            [
                BandMessageEvent(
                    message_id="m-seen",
                    content="AUTO:START WL-INC-001",
                    author_handle="human",
                ),
                BandMessageEvent(
                    message_id="m-new",
                    content="@unknown AUTO:START WL-INC-001",
                    author_handle="human",
                ),
            ]
        )

        output = io.StringIO()
        with redirect_stdout(output):
            runtime.print_receive_diagnostics(batch)

        diagnostics = output.getvalue()
        self.assertIn("batch_seen_order=m-seen:seen, m-new:new", diagnostics)
        self.assertIn("seen_messages_suppressed=1", diagnostics)
        self.assertIn("message_id=m-new seen_status=new", diagnostics)
        self.assertNotIn("message_id=m-seen seen_status=seen", diagnostics)

    def test_debug_receive_reports_human_only_batch(self) -> None:
        runtime = self._runtime_with_empty_source()
        output = io.StringIO()
        with redirect_stdout(output):
            runtime.print_receive_diagnostics(
                [
                    BandMessageEvent(
                        message_id="m-human-only",
                        content="AUTO:START WL-INC-001",
                        author_handle="human",
                    )
                ]
            )

        diagnostics = output.getvalue()
        self.assertIn(
            "No agent-authored messages visible in receive batch",
            diagnostics,
        )
        self.assertIn(
            "Latest batch contains only human-authored messages",
            diagnostics,
        )

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
                "--include-seen-debug",
                "--dump-recent-messages",
                "--message-limit",
                "25",
            ]
        )

        self.assertEqual(args.poll_interval, 7.5)
        self.assertEqual(args.run_id, "manual-run")
        self.assertFalse(args.stop_after_complete)
        self.assertTrue(args.single_pass)
        self.assertTrue(args.debug_receive)
        self.assertTrue(args.include_seen_debug)
        self.assertTrue(args.dump_recent_messages)
        self.assertEqual(args.message_limit, 25)

    def test_live_runtime_receives_poll_interval_and_single_pass(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        settings_obj.band_chat_id = "placeholder-chat-id"
        settings_obj.band_triage_agent_api_key = "placeholder-triage-key"

        runtime = build_runtime_from_settings(
            dry_run=False,
            poll_interval_seconds=6.0,
            single_pass=True,
            message_limit=25,
            settings_obj=settings_obj,
        )

        self.assertIsInstance(runtime.event_source, LiveBandEventSource)
        assert isinstance(runtime.event_source, LiveBandEventSource)
        self.assertEqual(runtime.event_source.poll_interval_seconds, 6.0)
        self.assertTrue(runtime.event_source.single_pass)
        self.assertEqual(runtime.event_source.message_limit, 25)

    def test_live_event_source_does_not_yield_old_start_message_repeatedly(self) -> None:
        old_start = BandMessageEvent(
            message_id="m-old-start",
            content="@triage AUTO:START WL-INC-001",
            author_handle="human",
        )
        new_agent_message = BandMessageEvent(
            message_id="m-new-triage",
            content="[WL-AUTO:WL-INC-001:triage:unit] @threat @forensics",
            author_handle="triage",
        )
        source = _PollingSequenceLiveBandEventSource(
            [
                [old_start],
                [old_start, new_agent_message],
            ]
        )

        async def collect_two_message_ids():
            message_ids = []
            async for event in source.events():
                message_ids.append(event.message_id)
                if len(message_ids) == 2:
                    break
            return message_ids

        self.assertEqual(
            asyncio.run(collect_two_message_ids()),
            ["m-old-start", "m-new-triage"],
        )

    def test_live_human_start_drives_full_internal_queue_chain(self) -> None:
        runtime, messenger, _source = self._live_internal_queue_runtime()

        state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.status, "complete")
        self.assertEqual(
            state.completed_roles,
            ["triage", "threat_intel", "forensics", "compliance", "commander"],
        )
        self.assertEqual(
            [message.role for message in messenger.sent_messages],
            ["triage", "threat_intel", "forensics", "compliance", "commander"],
        )

    def test_internal_event_ids_are_processed_once_per_role(self) -> None:
        runtime, _messenger, _source = self._live_internal_queue_runtime(
            run_id="internal-unit"
        )

        state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.processed_message_ids["triage"], ["m-human-start"])
        self.assertEqual(
            state.processed_message_ids["threat_intel"],
            ["internal:internal-unit:triage:1"],
        )
        self.assertEqual(
            state.processed_message_ids["forensics"],
            ["internal:internal-unit:triage:1"],
        )
        self.assertEqual(
            state.processed_message_ids["compliance"],
            [
                "internal:internal-unit:threat_intel:2",
                "internal:internal-unit:forensics:3",
            ],
        )
        self.assertEqual(
            state.processed_message_ids["commander"],
            ["internal:internal-unit:compliance:4"],
        )
        for message_ids in state.processed_message_ids.values():
            self.assertEqual(len(message_ids), len(set(message_ids)))

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
        settings_obj: Settings | None = None,
    ) -> AutonomousBandRuntime:
        settings_obj = settings_obj or self._settings_without_provider_keys()
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

    def _live_internal_queue_runtime(
        self,
        run_id: str = "internal-unit",
    ):
        settings_obj = self._settings_without_provider_keys()
        registry = build_band_remote_agent_registry(settings_obj)
        start = BandMessageEvent(
            message_id="m-human-start",
            content=f"@{registry['triage'].handle} AUTO:START WL-INC-001",
            author_handle="human",
            mention_handles=(registry["triage"].handle,),
        )
        source = _PollingSequenceLiveBandEventSource([[start]])
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
            run_id=run_id,
            settings_obj=settings_obj,
        )
        return runtime, messenger, source

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


class _PollingSequenceLiveBandEventSource(LiveBandEventSource):
    def __init__(self, batches: list[list[BandMessageEvent]]) -> None:
        super().__init__(
            base_url="https://band.example/api",
            chat_id="chat",
            agent_api_key="key",
            poll_interval_seconds=0,
            single_pass=False,
        )
        self._batches = list(batches)

    async def poll_once(self) -> list[BandMessageEvent]:
        if not self._batches:
            return []
        return self._batches.pop(0)


if __name__ == "__main__":
    unittest.main()
