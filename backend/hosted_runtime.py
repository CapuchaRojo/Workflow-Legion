from __future__ import annotations

import asyncio
import json
import os
import re
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import settings  # noqa: E402
from app.services.autonomous_agent_state import (  # noqa: E402
    AutonomousRunState,
    build_frontend_mission_control_export,
)
from app.services.band_client import BandConfigurationError  # noqa: E402
from run_autonomous_agents import build_runtime_from_args, parse_args  # noqa: E402


DEFAULT_STATE_DIR = ".workflow-legion-state"
DEFAULT_EXPORT_NAME = "mission-control-status.hosted.json"

SAFE_TOP_LEVEL_KEYS = (
    "schema_version",
    "source_state_file",
    "incident_id",
    "run_id",
    "chain_status",
    "current_chain",
    "current_role",
    "roles",
    "provider_stack",
    "final_commander_decision",
    "band_proof_note",
    "internal_queue_note",
    "created_at",
    "updated_at",
)
SAFE_ROLE_KEYS = (
    "role",
    "display_name",
    "status",
    "provider",
    "provider_mode",
    "summary",
    "handoff_targets",
    "delivery",
    "completed_at",
)
SAFE_DELIVERY_KEYS = (
    "status",
    "delivered",
    "status_code",
    "detail",
    "attempted_at",
)


@dataclass(frozen=True)
class HostedRuntimeConfig:
    autostart: bool
    dry_run: bool
    incident_id: str
    state_dir: Path
    mission_control_export: Path
    max_turns: int
    poll_interval_seconds: float
    message_limit: int
    run_id: str | None
    stop_after_complete: bool
    baseline_existing_messages: bool
    debug_receive: bool
    restart_after_complete: bool
    restart_delay_seconds: float

    @classmethod
    def from_env(cls, autostart: bool | None = None) -> "HostedRuntimeConfig":
        state_dir = Path(os.getenv("HOSTED_RUNTIME_STATE_DIR", DEFAULT_STATE_DIR))
        export_path = Path(
            os.getenv(
                "HOSTED_RUNTIME_MISSION_CONTROL_EXPORT",
                str(state_dir / DEFAULT_EXPORT_NAME),
            )
        )
        return cls(
            autostart=(
                _env_bool("HOSTED_RUNTIME_AUTOSTART", True)
                if autostart is None
                else autostart
            ),
            dry_run=_env_bool("HOSTED_RUNTIME_DRY_RUN", False),
            incident_id=os.getenv("HOSTED_RUNTIME_INCIDENT", "WL-INC-001"),
            state_dir=state_dir,
            mission_control_export=export_path,
            max_turns=_env_int("HOSTED_RUNTIME_MAX_TURNS", 12),
            poll_interval_seconds=_env_float("HOSTED_RUNTIME_POLL_INTERVAL", 5.0),
            message_limit=_env_int("HOSTED_RUNTIME_MESSAGE_LIMIT", 25),
            run_id=os.getenv("HOSTED_RUNTIME_RUN_ID") or None,
            stop_after_complete=_env_bool("HOSTED_RUNTIME_STOP_AFTER_COMPLETE", True),
            baseline_existing_messages=_env_bool(
                "HOSTED_RUNTIME_BASELINE_EXISTING",
                True,
            ),
            debug_receive=_env_bool("HOSTED_RUNTIME_DEBUG_RECEIVE", False),
            restart_after_complete=_env_bool(
                "HOSTED_RUNTIME_RESTART_AFTER_COMPLETE",
                True,
            ),
            restart_delay_seconds=_env_float("HOSTED_RUNTIME_RESTART_DELAY", 2.0),
        )


def create_app(
    config: HostedRuntimeConfig | None = None,
    autostart: bool | None = None,
) -> FastAPI:
    resolved_config = config or HostedRuntimeConfig.from_env(autostart=autostart)

    @asynccontextmanager
    async def lifespan(lifespan_app: FastAPI):
        if not resolved_config.autostart:
            _set_runtime_status(lifespan_app, runtime_state="disabled")
            yield
            return

        task = asyncio.create_task(_runtime_supervisor(lifespan_app))
        lifespan_app.state.hosted_runtime_task = task
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title="Workflow Legion Hosted Runtime",
        description="Hosted Band listener and sanitized Mission Control status.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.state.hosted_runtime_config = resolved_config
    app.state.hosted_runtime_task = None
    app.state.hosted_runtime_status = _initial_runtime_status(resolved_config)

    @app.get("/health")
    def health() -> dict[str, Any]:
        runtime_status = dict(app.state.hosted_runtime_status)
        runtime_state = runtime_status.get("runtime_state")
        return {
            "status": "degraded"
            if runtime_state in {"config_error", "error"}
            else "ok",
            "service": "workflow-legion-hosted-runtime",
            "band_configured": bool(
                settings.band_chat_id and settings.band_triage_agent_api_key
            ),
            "autostart": resolved_config.autostart,
            "mission_control_status_available": (
                resolved_config.mission_control_export.exists()
                or (resolved_config.state_dir / "mission-control-status.json").exists()
            ),
            "runtime": runtime_status,
        }

    @app.get("/mission-control-status")
    def mission_control_status() -> dict[str, Any]:
        return load_mission_control_status(resolved_config)

    return app


async def _runtime_supervisor(app: FastAPI) -> None:
    config: HostedRuntimeConfig = app.state.hosted_runtime_config
    cycle = 0

    while True:
        cycle += 1
        _set_runtime_status(
            app,
            runtime_state="starting",
            cycle=cycle,
            last_error=None,
        )
        try:
            args = parse_args(_runtime_argv(config))
            runtime = build_runtime_from_args(args)
            runtime.enable_receive_debug(config.debug_receive)
            if config.debug_receive:
                runtime.print_startup_receive_diagnostics()

            _set_runtime_status(
                app,
                runtime_state="listening",
                cycle=cycle,
                run_id=runtime.run_id,
            )
            state = await runtime.run_until_complete()
            _set_runtime_status(
                app,
                runtime_state=state.status,
                cycle=cycle,
                incident_id=state.incident_id,
                run_id=state.run_id,
                completed_roles=list(state.completed_roles),
                completed_at=_utc_now_iso(),
            )
            if not config.restart_after_complete:
                return

            await asyncio.sleep(config.restart_delay_seconds)
        except asyncio.CancelledError:
            _set_runtime_status(app, runtime_state="stopped", stopped_at=_utc_now_iso())
            raise
        except BandConfigurationError as exc:
            _set_runtime_status(
                app,
                runtime_state="config_error",
                cycle=cycle,
                last_error=_safe_error(exc),
            )
            return
        except Exception as exc:
            _set_runtime_status(
                app,
                runtime_state="error",
                cycle=cycle,
                last_error=_safe_error(exc),
            )
            if not config.restart_after_complete:
                return
            await asyncio.sleep(config.restart_delay_seconds)


def load_mission_control_status(config: HostedRuntimeConfig) -> dict[str, Any]:
    for path in (
        config.mission_control_export,
        config.state_dir / "mission-control-status.json",
    ):
        payload = _read_json(path)
        if payload is None:
            continue
        if "roles" in payload:
            return sanitize_mission_control_payload(payload)
        if "role_outputs" in payload:
            state = _autonomous_state_from_payload(payload)
            return sanitize_mission_control_payload(
                build_frontend_mission_control_export(state)
            )

    return sanitize_mission_control_payload(
        build_frontend_mission_control_export(
            AutonomousRunState(
                incident_id=config.incident_id,
                run_id=config.run_id or "hosted-waiting",
            )
        )
    )


def sanitize_mission_control_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key in SAFE_TOP_LEVEL_KEYS:
        if key not in payload:
            continue
        value = payload[key]
        if key == "roles":
            sanitized[key] = [
                _sanitize_role(role)
                for role in value
                if isinstance(role, dict)
            ]
        elif key == "provider_stack":
            sanitized[key] = [
                _sanitize_provider_stack(item)
                for item in value
                if isinstance(item, dict)
            ]
        elif key == "final_commander_decision":
            sanitized[key] = _sanitize_final_decision(value)
        elif key == "source_state_file":
            sanitized[key] = ".workflow-legion-state/mission-control-status.json"
        else:
            sanitized[key] = value

    return sanitized


def _autonomous_state_from_payload(payload: dict[str, Any]) -> AutonomousRunState:
    allowed_keys = set(AutonomousRunState.__dataclass_fields__)
    state_payload = {
        key: value
        for key, value in payload.items()
        if key in allowed_keys
    }
    return AutonomousRunState.from_dict(state_payload)


def _sanitize_role(role: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key in SAFE_ROLE_KEYS:
        if key not in role:
            continue
        if key == "delivery":
            sanitized[key] = _sanitize_delivery(role[key])
        else:
            sanitized[key] = role[key]
    return sanitized


def _sanitize_delivery(delivery: Any) -> dict[str, Any]:
    if not isinstance(delivery, dict):
        return {}
    sanitized: dict[str, Any] = {}
    for key in SAFE_DELIVERY_KEYS:
        if key not in delivery:
            continue
        sanitized[key] = (
            _safe_text(delivery[key])
            if key == "detail"
            else delivery[key]
        )
    return sanitized


def _sanitize_provider_stack(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": item.get("provider"),
        "roles": item.get("roles", []),
    }


def _sanitize_final_decision(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"status": "pending", "summary": ""}
    return {
        "status": value.get("status", "pending"),
        "summary": value.get("summary", ""),
    }


def _runtime_argv(config: HostedRuntimeConfig) -> list[str]:
    argv = [
        "--incident",
        config.incident_id,
        "--state-dir",
        str(config.state_dir),
        "--frontend-studio-export",
        str(config.mission_control_export),
        "--max-turns",
        str(config.max_turns),
        "--poll-interval",
        str(config.poll_interval_seconds),
        "--message-limit",
        str(config.message_limit),
    ]
    if config.dry_run:
        argv.append("--dry-run")
    if config.run_id:
        argv.extend(["--run-id", config.run_id])
    if config.stop_after_complete:
        argv.append("--stop-after-complete")
    else:
        argv.append("--no-stop-after-complete")
    if config.baseline_existing_messages:
        argv.append("--ignore-existing")
    return argv


def _initial_runtime_status(config: HostedRuntimeConfig) -> dict[str, Any]:
    return {
        "runtime_state": "starting" if config.autostart else "disabled",
        "cycle": 0,
        "incident_id": config.incident_id,
        "run_id": config.run_id,
        "completed_roles": [],
        "started_at": _utc_now_iso(),
        "completed_at": None,
        "stopped_at": None,
        "last_error": None,
    }


def _set_runtime_status(app: FastAPI, **updates: Any) -> None:
    status = dict(app.state.hosted_runtime_status)
    status.update(updates)
    status["updated_at"] = _utc_now_iso()
    app.state.hosted_runtime_status = status


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _safe_error(exc: Exception) -> str:
    return _safe_text(str(exc))


def _safe_text(value: Any) -> str:
    text = " ".join(str(value).split())
    text = re.sub(
        r"(?i)\b(api[_-]?key|token|authorization)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)\bbearer\s+[A-Za-z0-9._\-/]+",
        "Bearer [REDACTED]",
        text,
    )
    return text[:240]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


app = create_app()
