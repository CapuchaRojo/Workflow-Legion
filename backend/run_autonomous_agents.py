from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys
from typing import Sequence


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.autonomous_band_runtime import build_runtime_from_settings  # noqa: E402
from app.services.autonomous_role_agents import ROLE_DEFINITIONS  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Workflow Legion autonomous Band task-agent runtime.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate Band receive/send events locally without live Band calls.",
    )
    parser.add_argument(
        "--incident",
        default="WL-INC-001",
        help="Incident ID to start in dry-run mode.",
    )
    parser.add_argument(
        "--state-dir",
        default=".workflow-legion-state",
        help="Directory for autonomous runtime state files.",
    )
    parser.add_argument(
        "--frontend-studio-export",
        default=None,
        help=(
            "Optional sanitized Mission Control JSON export path for the "
            "frontend showcase."
        ),
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=12,
        help="Maximum role turns before the runtime stops.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Seconds between live Band receive polls.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional explicit run ID for WL-AUTO markers.",
    )
    stop_group = parser.add_mutually_exclusive_group()
    stop_group.add_argument(
        "--stop-after-complete",
        dest="stop_after_complete",
        action="store_true",
        default=True,
        help="Exit cleanly after Commander posts the final decision.",
    )
    stop_group.add_argument(
        "--no-stop-after-complete",
        dest="stop_after_complete",
        action="store_false",
        help="Keep listening after Commander completes the current run.",
    )
    parser.add_argument(
        "--once",
        "--single-pass",
        dest="single_pass",
        action="store_true",
        help="Process currently available live Band messages once, then exit.",
    )
    parser.add_argument(
        "--debug-receive",
        action="store_true",
        help="Print safe live receive diagnostics without exposing credentials.",
    )
    parser.add_argument(
        "--include-seen-debug",
        action="store_true",
        help="When debug receive is enabled, include already-seen messages.",
    )
    parser.add_argument(
        "--dump-recent-messages",
        action="store_true",
        help=(
            "Fetch one recent Band message batch, print safe summaries, and exit "
            "without posting agent replies."
        ),
    )
    parser.add_argument(
        "--message-limit",
        type=int,
        default=5,
        help="Maximum recent Band messages to fetch per receive poll.",
    )
    return parser.parse_args(argv)


async def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    runtime = build_runtime_from_settings(
        dry_run=args.dry_run,
        incident_id=args.incident,
        state_dir=args.state_dir,
        frontend_studio_export=args.frontend_studio_export,
        max_turns=args.max_turns,
        poll_interval_seconds=args.poll_interval,
        run_id=args.run_id,
        stop_after_complete=args.stop_after_complete,
        single_pass=args.single_pass,
        message_limit=args.message_limit,
    )
    runtime.enable_receive_debug(
        args.debug_receive,
        include_seen_debug=args.include_seen_debug,
    )

    if args.debug_receive:
        runtime.print_startup_receive_diagnostics()

    if args.dump_recent_messages:
        if not args.single_pass:
            print("Dump mode is read-only and uses one receive batch.")
        await runtime.dump_recent_messages(message_limit=args.message_limit)
        return 0

    if args.dry_run:
        print(
            f"[dry-run] human -> @{runtime.registry['triage'].handle} "
            f"AUTO:START {args.incident}"
        )
    else:
        print(
            "Listening for Band mention events. "
            f"Poll interval: {args.poll_interval:g}s. "
            "Stop condition: Commander final decision."
        )
        if args.single_pass:
            print("Single-pass mode enabled: processing current messages once.")

    state = await runtime.run_until_complete()

    for role in state.completed_roles:
        output = state.role_outputs[role]
        targets = output.handoff_roles
        if targets:
            target_names = " + ".join(_display_role(target) for target in targets)
            print(f"{_display_role(role)} -> {target_names}")
        else:
            print(f"{_display_role(role)} -> stop")

    print(
        "Chain: Triage -> Threat Intel + Forensics -> Compliance -> Commander -> stop"
    )
    print(f"Status: {state.status}")
    print(f"Run ID: {state.run_id}")
    print(f"State file: {runtime.state_store.path_for(state.incident_id, state.run_id)}")
    print(f"Mission Control state: {runtime.state_store.mission_control_path()}")
    if runtime.state_store.frontend_export_path:
        print(f"Frontend Studio export: {runtime.state_store.frontend_export_path}")
    return 0 if state.status == "complete" else 1


def run_cli(argv: Sequence[str] | None = None) -> int:
    try:
        return asyncio.run(main(argv))
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Autonomous runtime stopped by operator.")
        return 130


def _display_role(role: str) -> str:
    if role not in ROLE_DEFINITIONS:
        return role
    return ROLE_DEFINITIONS[role].display_name.replace(" Agent", "")


if __name__ == "__main__":
    raise SystemExit(run_cli())
