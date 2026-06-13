from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTONOMOUS_STATE_DIR = ".workflow-legion-state"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RoleOutputRecord:
    role: str
    provider_name: str
    provider_mode: str
    summary: str
    evidence: list[str]
    recommended_actions: list[str]
    handoff_roles: list[str]
    band_message: str
    source_message_ids: list[str]
    completed_at: str = field(default_factory=utc_now_iso)


@dataclass
class AutonomousRunState:
    incident_id: str
    run_id: str
    status: str = "waiting"
    processed_message_ids: dict[str, list[str]] = field(default_factory=dict)
    completed_roles: list[str] = field(default_factory=list)
    role_outputs: dict[str, RoleOutputRecord] = field(default_factory=dict)
    provider_mode_by_role: dict[str, str] = field(default_factory=dict)
    pending_role_message_ids: dict[str, list[str]] = field(default_factory=dict)
    turn_count: int = 0
    max_turns: int = 12
    final_decision_state: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def mark_processed(self, role: str, message_id: str) -> bool:
        processed = self.processed_message_ids.setdefault(role, [])
        if message_id in processed:
            return False

        processed.append(message_id)
        self.updated_at = utc_now_iso()
        return True

    def was_processed(self, role: str, message_id: str) -> bool:
        return message_id in self.processed_message_ids.get(role, [])

    def add_pending_message(self, role: str, message_id: str) -> None:
        pending = self.pending_role_message_ids.setdefault(role, [])
        if message_id not in pending:
            pending.append(message_id)
            self.updated_at = utc_now_iso()

    def complete_role(self, output: RoleOutputRecord) -> None:
        if output.role not in self.completed_roles:
            self.completed_roles.append(output.role)

        self.role_outputs[output.role] = output
        self.provider_mode_by_role[output.role] = output.provider_mode
        self.pending_role_message_ids.pop(output.role, None)
        self.turn_count += 1
        self.status = "complete" if output.role == "commander" else "running"

        if output.role == "commander":
            self.final_decision_state = output.summary

        self.updated_at = utc_now_iso()

    def completed(self, role: str) -> bool:
        return role in self.completed_roles

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["role_outputs"] = {
            role: asdict(output)
            for role, output in self.role_outputs.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AutonomousRunState":
        role_outputs = {
            role: RoleOutputRecord(**output)
            for role, output in data.get("role_outputs", {}).items()
        }
        payload = dict(data)
        payload["role_outputs"] = role_outputs
        return cls(**payload)


class AutonomousStateStore:
    def __init__(self, state_dir: str | Path = AUTONOMOUS_STATE_DIR) -> None:
        self.state_dir = Path(state_dir)

    def path_for(self, incident_id: str, run_id: str) -> Path:
        safe_incident = _safe_path_token(incident_id)
        safe_run = _safe_path_token(run_id)
        return self.state_dir / f"{safe_incident}-{safe_run}.json"

    def mission_control_path(self) -> Path:
        return self.state_dir / "mission-control-status.json"

    def save(self, state: AutonomousRunState) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state.to_dict(), indent=2, sort_keys=True)
        self.path_for(state.incident_id, state.run_id).write_text(
            payload,
            encoding="utf-8",
        )
        self.mission_control_path().write_text(payload, encoding="utf-8")

    def load(self, incident_id: str, run_id: str) -> AutonomousRunState | None:
        path = self.path_for(incident_id, run_id)
        if not path.exists():
            return None

        return AutonomousRunState.from_dict(json.loads(path.read_text("utf-8")))


def _safe_path_token(value: str) -> str:
    return "".join(
        character if character.isalnum() or character in ("-", "_") else "-"
        for character in value
    )
