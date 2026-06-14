import asyncio
import io
import json
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
    LiveBandMessenger,
    ScriptedBandEventSource,
    SentBandMessage,
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
    AutonomousRoleOutput,
)
from app.services.band_agent_registry import build_band_remote_agent_registry  # noqa: E402
from app.services.band_client import BandDeliveryResult  # noqa: E402
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
                "--ignore-existing",
                "--frontend-studio-export",
                "frontend-showcase\\public\\mission-control-status.json",
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
        self.assertTrue(args.baseline_existing)
        self.assertEqual(
            args.frontend_studio_export,
            "frontend-showcase\\public\\mission-control-status.json",
        )

    def test_baseline_existing_cli_alias_parses(self) -> None:
        args = parse_args(["--baseline-existing"])

        self.assertTrue(args.baseline_existing)

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
        self.assertFalse(runtime.event_source.baseline_existing_messages)

    def test_live_runtime_receives_baseline_existing_option(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        settings_obj.band_chat_id = "placeholder-chat-id"
        settings_obj.band_triage_agent_api_key = "placeholder-triage-key"

        runtime = build_runtime_from_settings(
            dry_run=False,
            message_limit=25,
            baseline_existing_messages=True,
            settings_obj=settings_obj,
        )

        self.assertIsInstance(runtime.event_source, LiveBandEventSource)
        assert isinstance(runtime.event_source, LiveBandEventSource)
        self.assertTrue(runtime.event_source.baseline_existing_messages)
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

    def test_live_without_baseline_processes_first_auto_message(self) -> None:
        runtime, messenger, _source = self._live_internal_queue_runtime(
            run_id="no-baseline-unit"
        )

        state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.status, "complete")
        self.assertEqual(state.processed_message_ids["triage"], ["m-human-start"])
        self.assertEqual(messenger.sent_messages[0].role, "triage")

    def test_live_baseline_marks_first_batch_seen_without_processing(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        registry = build_band_remote_agent_registry(settings_obj)
        historical_start = BandMessageEvent(
            message_id="m-historical-start",
            content=f"@{registry['triage'].handle} AUTO:START WL-INC-001",
            author_handle="human",
            mention_handles=(registry["triage"].handle,),
        )
        source = _PollingSequenceLiveBandEventSource(
            [[historical_start], []],
            baseline_existing_messages=True,
            single_pass=True,
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
            run_id="baseline-only-unit",
            settings_obj=settings_obj,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "stopped before a run was started",
        ):
            asyncio.run(runtime.run_until_complete())

        self.assertIsNone(runtime.state)
        self.assertEqual(messenger.sent_messages, [])
        self.assertIn("m-historical-start", source._seen_message_ids)

    def test_live_baseline_allows_later_fresh_auto_message(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        registry = build_band_remote_agent_registry(settings_obj)
        historical_start = BandMessageEvent(
            message_id="m-historical-start",
            content=f"@{registry['triage'].handle} AUTO:START WL-INC-001",
            author_handle="human",
            mention_handles=(registry["triage"].handle,),
        )
        fresh_start = BandMessageEvent(
            message_id="m-fresh-start",
            content=f"@{registry['triage'].handle} AUTO:START WL-INC-001",
            author_handle="human",
            mention_handles=(registry["triage"].handle,),
        )
        source = _PollingSequenceLiveBandEventSource(
            [[historical_start], [historical_start, fresh_start]],
            baseline_existing_messages=True,
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
            run_id="baseline-fresh-unit",
            settings_obj=settings_obj,
        )

        state = asyncio.run(runtime.run_until_complete())

        self.assertEqual(state.status, "complete")
        self.assertEqual(state.processed_message_ids["triage"], ["m-fresh-start"])
        self.assertNotIn("m-historical-start", state.processed_message_ids["triage"])
        self.assertIn("m-historical-start", source._seen_message_ids)
        self.assertIn("m-fresh-start", source._seen_message_ids)

    def test_live_baseline_debug_output_is_sanitized(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        registry = build_band_remote_agent_registry(settings_obj)
        historical_start = BandMessageEvent(
            message_id="m-baseline-history",
            content=(
                f"@{registry['triage'].handle} AUTO:START WL-INC-001 "
                "do-not-print-marker"
            ),
            author_handle="human",
            mention_handles=(registry["triage"].handle,),
        )
        fresh_start = BandMessageEvent(
            message_id="m-baseline-fresh",
            content=f"@{registry['triage'].handle} AUTO:START WL-INC-001",
            author_handle="human",
            mention_handles=(registry["triage"].handle,),
        )
        source = _PollingSequenceLiveBandEventSource(
            [[historical_start], [fresh_start]],
            baseline_existing_messages=True,
        )
        runtime = AutonomousBandRuntime(
            registry=registry,
            event_source=source,
            messenger=DryRunBandMessenger(registry),
            reasoning_provider=AutonomousReasoningProvider(
                provider_mode="deterministic",
                settings_obj=settings_obj,
            ),
            state_store=AutonomousStateStore(tempfile.mkdtemp()),
            run_id="baseline-debug-unit",
            settings_obj=settings_obj,
        )
        runtime.enable_receive_debug(True)

        output = io.StringIO()
        with redirect_stdout(output):
            runtime.print_startup_receive_diagnostics()
            asyncio.run(runtime.run_until_complete())

        diagnostics = output.getvalue()
        self.assertIn("baseline_existing_messages=True", diagnostics)
        self.assertIn("baselined_existing_message_count=1", diagnostics)
        self.assertNotIn("do-not-print-marker", diagnostics)

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

    def test_live_commander_final_post_uses_audit_only_visible_mention(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        settings_obj.band_chat_id = "placeholder-chat-id"
        settings_obj.band_commander_agent_api_key = "placeholder-commander-key"
        registry = build_band_remote_agent_registry(settings_obj)
        client = _CapturingBandClient()
        output = AutonomousRoleOutput(
            role="commander",
            provider_name="featherless",
            provider_mode="deterministic_fallback",
            summary="Final containment decision.",
            evidence=(),
            recommended_actions=(),
            handoff_roles=("Stop",),
            band_message="[WL-AUTO:WL-INC-001:commander:unit] Final decision.",
        )

        with patch(
            "app.services.autonomous_band_runtime.build_band_client_for_agent",
            return_value=client,
        ):
            sent_message = asyncio.run(
                LiveBandMessenger(settings_obj, registry).send_role_output(
                    "commander",
                    output,
                )
            )

        compliance_handle = registry["compliance"].handle
        self.assertEqual(sent_message.mention_handles, (compliance_handle,))
        self.assertEqual(sent_message.workflow_handoff_roles, ())
        self.assertEqual(
            sent_message.terminal_audit_mention_handles,
            (compliance_handle,),
        )
        self.assertEqual(client.calls[0]["mention_handles"], [compliance_handle])
        self.assertEqual(
            client.calls[0]["content"],
            "[WL-AUTO:WL-INC-001:commander:unit] Final decision.",
        )

    def test_commander_terminal_stop_success_marks_runtime_complete(self) -> None:
        runtime, messenger, start = self._delivery_sequence_runtime(
            [True, True, True, True, True],
            reasoning_provider=_TerminalStopReasoningProvider(
                self._settings_without_provider_keys()
            ),
        )

        asyncio.run(runtime.handle_event(start))
        asyncio.run(runtime._drain_internal_events())

        assert runtime.state is not None
        self.assertEqual(runtime.state.status, "complete")
        self.assertIn("commander", runtime.state.completed_roles)
        self.assertIsNotNone(runtime.state.final_decision_state)
        self.assertEqual(runtime.state.role_outputs["commander"].handoff_roles, [])
        self.assertEqual(messenger.sent_messages[-1].role, "commander")
        self.assertEqual(
            messenger.sent_messages[-1].mention_handles,
            (runtime.registry["compliance"].handle,),
        )
        self.assertEqual(messenger.sent_messages[-1].workflow_handoff_roles, ())
        self.assertEqual(
            messenger.sent_messages[-1].terminal_audit_mention_handles,
            (runtime.registry["compliance"].handle,),
        )
        self.assertEqual(len(runtime._internal_events), 0)

    def test_commander_terminal_stop_failed_band_post_stays_incomplete(self) -> None:
        runtime, messenger, start = self._delivery_sequence_runtime(
            [True, True, True, True, False],
            reasoning_provider=_TerminalStopReasoningProvider(
                self._settings_without_provider_keys()
            ),
        )

        asyncio.run(runtime.handle_event(start))
        asyncio.run(runtime._drain_internal_events())

        assert runtime.state is not None
        self.assertNotIn("commander", runtime.state.completed_roles)
        self.assertNotEqual(runtime.state.status, "complete")
        self.assertIsNone(runtime.state.final_decision_state)
        self.assertEqual(messenger.sent_messages[-1].role, "commander")
        self.assertEqual(
            messenger.sent_messages[-1].mention_handles,
            (runtime.registry["compliance"].handle,),
        )
        self.assertEqual(messenger.sent_messages[-1].workflow_handoff_roles, ())
        self.assertEqual(
            runtime.state.delivery_status_by_role["commander"].status,
            "failed",
        )

    def test_stop_terminal_target_is_not_exported_as_remote_band_agent(self) -> None:
        runtime, _messenger, start = self._delivery_sequence_runtime(
            [True, True, True, True, True],
            reasoning_provider=_TerminalStopReasoningProvider(
                self._settings_without_provider_keys()
            ),
        )

        with tempfile.TemporaryDirectory() as state_dir:
            export_path = Path(state_dir) / "mission-control-status.json"
            runtime.state_store = AutonomousStateStore(
                state_dir,
                frontend_export_path=export_path,
            )

            asyncio.run(runtime.handle_event(start))
            asyncio.run(runtime._drain_internal_events())
            exported = json.loads(export_path.read_text("utf-8"))

        commander = next(
            role for role in exported["roles"] if role["role"] == "commander"
        )
        self.assertEqual(commander["handoff_targets"], [])
        self.assertEqual(exported["final_commander_decision"]["status"], "complete")

    def test_final_decision_terminal_target_is_not_a_remote_handoff(self) -> None:
        runtime, messenger, start = self._delivery_sequence_runtime(
            [True, True, True, True, True],
            reasoning_provider=_TerminalStopReasoningProvider(
                self._settings_without_provider_keys(),
                terminal_target="final_decision",
            ),
        )

        asyncio.run(runtime.handle_event(start))
        asyncio.run(runtime._drain_internal_events())

        assert runtime.state is not None
        self.assertEqual(runtime.state.status, "complete")
        self.assertEqual(runtime.state.role_outputs["commander"].handoff_roles, [])
        self.assertEqual(messenger.sent_messages[-1].workflow_handoff_roles, ())
        self.assertEqual(
            messenger.sent_messages[-1].mention_handles,
            (runtime.registry["compliance"].handle,),
        )
        self.assertEqual(len(runtime._internal_events), 0)

    def test_failed_triage_band_post_does_not_complete_role(self) -> None:
        runtime, messenger, start = self._delivery_sequence_runtime([False])

        asyncio.run(runtime.handle_event(start))

        assert runtime.state is not None
        self.assertNotIn("triage", runtime.state.completed_roles)
        self.assertNotIn("triage", runtime.state.role_outputs)
        self.assertEqual(runtime.state.pending_role_message_ids["triage"], ["m-human-start"])
        self.assertEqual([message.role for message in messenger.sent_messages], ["triage"])

    def test_failed_triage_band_post_does_not_enqueue_downstream_events(self) -> None:
        runtime, messenger, start = self._delivery_sequence_runtime([False])

        asyncio.run(runtime.handle_event(start))
        asyncio.run(runtime._drain_internal_events())

        assert runtime.state is not None
        self.assertEqual([message.role for message in messenger.sent_messages], ["triage"])
        self.assertEqual(len(runtime._internal_events), 0)
        self.assertNotIn("threat_intel", runtime.state.processed_message_ids)
        self.assertNotIn("forensics", runtime.state.processed_message_ids)

    def test_failed_triage_band_post_can_complete_on_later_successful_retry(self) -> None:
        runtime, messenger, start = self._delivery_sequence_runtime([False, True])

        asyncio.run(runtime.handle_event(start))
        retry_start = BandMessageEvent(
            message_id="m-human-start-retry",
            content=start.content,
            author_handle=start.author_handle,
            mention_handles=start.mention_handles,
        )
        asyncio.run(runtime.handle_event(retry_start))

        assert runtime.state is not None
        self.assertEqual(runtime.state.completed_roles, ["triage"])
        self.assertEqual(
            [message.delivery.delivered for message in messenger.sent_messages],
            [False, True],
        )
        self.assertEqual(
            runtime.state.role_outputs["triage"].source_message_ids,
            ["m-human-start", "m-human-start-retry"],
        )

    def test_failed_commander_band_post_does_not_complete_runtime(self) -> None:
        runtime, messenger, start = self._delivery_sequence_runtime(
            [True, True, True, True, False]
        )

        asyncio.run(runtime.handle_event(start))
        asyncio.run(runtime._drain_internal_events())

        assert runtime.state is not None
        self.assertEqual(
            runtime.state.completed_roles,
            ["triage", "threat_intel", "forensics", "compliance"],
        )
        self.assertNotEqual(runtime.state.status, "complete")
        self.assertIsNone(runtime.state.final_decision_state)
        self.assertEqual(
            [message.role for message in messenger.sent_messages],
            ["triage", "threat_intel", "forensics", "compliance", "commander"],
        )

    def test_frontend_studio_export_contains_only_sanitized_status(self) -> None:
        settings_obj = self._settings_without_provider_keys()
        configured_agent_ids = [
            "configured-triage-agent-id",
            "configured-threat-agent-id",
            "configured-forensics-agent-id",
            "configured-compliance-agent-id",
            "configured-commander-agent-id",
        ]
        (
            settings_obj.band_triage_agent_id,
            settings_obj.band_threat_intel_agent_id,
            settings_obj.band_forensics_agent_id,
            settings_obj.band_compliance_agent_id,
            settings_obj.band_commander_agent_id,
        ) = configured_agent_ids

        with tempfile.TemporaryDirectory() as state_dir:
            export_path = Path(state_dir) / "mission-control-status.json"
            runtime = build_runtime_from_settings(
                dry_run=True,
                incident_id="WL-INC-001",
                state_dir=state_dir,
                frontend_studio_export=str(export_path),
                run_id="studio-safe",
                settings_obj=settings_obj,
            )

            asyncio.run(runtime.run_until_complete())

            exported_text = export_path.read_text("utf-8")
            exported = json.loads(exported_text)

        self.assertEqual(exported["incident_id"], "WL-INC-001")
        self.assertEqual(exported["run_id"], "studio-safe")
        self.assertEqual(exported["chain_status"], "complete")
        self.assertEqual(exported["final_commander_decision"]["status"], "complete")
        self.assertEqual(len(exported["roles"]), 5)
        self.assertNotIn("agent_id", exported_text.lower())
        self.assertNotIn("api_key", exported_text.lower())
        self.assertNotIn("chat_id", exported_text.lower())
        self.assertNotIn("room_id", exported_text.lower())
        for configured_agent_id in configured_agent_ids:
            self.assertNotIn(configured_agent_id, exported_text)
        for key in self._nested_keys(exported):
            lowered = key.lower()
            self.assertNotIn("key", lowered)
            self.assertNotIn("agent_id", lowered)
            self.assertNotIn("chat_id", lowered)
            self.assertNotIn("room_id", lowered)

    def test_failed_band_delivery_exports_failed_not_complete(self) -> None:
        runtime, _messenger, start = self._delivery_sequence_runtime([False])

        with tempfile.TemporaryDirectory() as state_dir:
            export_path = Path(state_dir) / "mission-control-status.json"
            runtime.state_store = AutonomousStateStore(
                state_dir,
                frontend_export_path=export_path,
            )

            asyncio.run(runtime.handle_event(start))

            exported = json.loads(export_path.read_text("utf-8"))

        triage = next(role for role in exported["roles"] if role["role"] == "triage")
        self.assertEqual(triage["status"], "failed")
        self.assertEqual(triage["delivery"]["status"], "failed")
        self.assertFalse(triage["delivery"]["delivered"])
        self.assertNotEqual(exported["chain_status"], "complete")

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

    def _nested_keys(self, value):
        if isinstance(value, dict):
            for key, child in value.items():
                yield str(key)
                yield from self._nested_keys(child)
        elif isinstance(value, list):
            for child in value:
                yield from self._nested_keys(child)

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

    def _delivery_sequence_runtime(
        self,
        delivered_results: list[bool],
        run_id: str = "delivery-unit",
        reasoning_provider=None,
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
        messenger = _SequencedDeliveryBandMessenger(registry, delivered_results)
        runtime = AutonomousBandRuntime(
            registry=registry,
            event_source=source,
            messenger=messenger,
            reasoning_provider=reasoning_provider
            or AutonomousReasoningProvider(
                provider_mode="deterministic",
                settings_obj=settings_obj,
            ),
            state_store=AutonomousStateStore(tempfile.mkdtemp()),
            run_id=run_id,
            settings_obj=settings_obj,
        )
        return runtime, messenger, start

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
    def __init__(
        self,
        batches: list[list[BandMessageEvent]],
        baseline_existing_messages: bool = False,
        single_pass: bool = False,
    ) -> None:
        super().__init__(
            base_url="https://band.example/api",
            chat_id="chat",
            agent_api_key="key",
            poll_interval_seconds=0,
            single_pass=single_pass,
            baseline_existing_messages=baseline_existing_messages,
        )
        self._batches = list(batches)

    async def poll_once(self) -> list[BandMessageEvent]:
        if not self._batches:
            return []
        return self._batches.pop(0)


class _SequencedDeliveryBandMessenger:
    def __init__(
        self,
        registry,
        delivered_results: list[bool],
    ) -> None:
        self.registry = registry
        self.delivered_results = list(delivered_results)
        self.sent_messages: list[SentBandMessage] = []

    async def send_role_output(self, role, output) -> SentBandMessage:
        delivered = self.delivered_results.pop(0)
        workflow_handoff_roles = tuple(
            target for target in output.handoff_roles if target in self.registry
        )
        mention_handles = tuple(
            self.registry[target].handle for target in workflow_handoff_roles
        )
        if role == "commander" and not mention_handles:
            mention_handles = (self.registry["compliance"].handle,)
        workflow_handles = {
            self.registry[target].handle for target in workflow_handoff_roles
        }
        message = SentBandMessage(
            message_id=f"sequenced-{len(self.sent_messages) + 1}-{role}",
            role=role,
            content=output.band_message,
            mention_handles=mention_handles,
            delivery=BandDeliveryResult(
                delivered=delivered,
                detail="Sequenced test delivery result.",
                status_code=200 if delivered else 503,
            ),
            workflow_handoff_roles=workflow_handoff_roles,
            terminal_audit_mention_handles=tuple(
                handle for handle in mention_handles if handle not in workflow_handles
            ),
        )
        self.sent_messages.append(message)
        return message


class _TerminalStopReasoningProvider(AutonomousReasoningProvider):
    def __init__(
        self,
        settings_obj: Settings,
        terminal_target: str = "Stop",
    ) -> None:
        super().__init__(
            provider_mode="deterministic",
            settings_obj=settings_obj,
        )
        self.terminal_target = terminal_target

    async def decide(self, definition, context):
        output = await super().decide(definition, context)
        if definition.role != "commander":
            return output

        return AutonomousRoleOutput(
            role=output.role,
            provider_name=output.provider_name,
            provider_mode=output.provider_mode,
            summary=output.summary,
            evidence=output.evidence,
            recommended_actions=output.recommended_actions,
            handoff_roles=(self.terminal_target,),
            band_message=output.band_message,
        )


class _CapturingBandClient:
    def __init__(self) -> None:
        self.calls = []

    async def send_text_message(self, chat_id, content, mention_handles=None):
        self.calls.append(
            {
                "chat_id": chat_id,
                "content": content,
                "mention_handles": mention_handles,
            }
        )
        return BandDeliveryResult(
            delivered=True,
            detail="Captured.",
            status_code=201,
        )


if __name__ == "__main__":
    unittest.main()
