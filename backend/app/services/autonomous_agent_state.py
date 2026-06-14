from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.autonomous_role_agents import (
    ROLE_DEFINITIONS,
    ROLE_ORDER,
    UPSTREAM_ROLES,
)


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
class RoleDeliveryRecord:
    role: str
    delivered: bool
    status: str
    status_code: int | None = None
    detail: str | None = None
    attempted_at: str = field(default_factory=utc_now_iso)


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
    delivery_status_by_role: dict[str, RoleDeliveryRecord] = field(default_factory=dict)
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

    def record_delivery(
        self,
        role: str,
        delivered: bool,
        status_code: int | None = None,
        detail: str | None = None,
    ) -> None:
        self.delivery_status_by_role[role] = RoleDeliveryRecord(
            role=role,
            delivered=delivered,
            status="delivered" if delivered else "failed",
            status_code=status_code,
            detail=_safe_delivery_detail(detail) if not delivered else None,
        )
        self.updated_at = utc_now_iso()

    def completed(self, role: str) -> bool:
        return role in self.completed_roles

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["role_outputs"] = {
            role: asdict(output)
            for role, output in self.role_outputs.items()
        }
        data["delivery_status_by_role"] = {
            role: asdict(delivery)
            for role, delivery in self.delivery_status_by_role.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AutonomousRunState":
        role_outputs = {
            role: RoleOutputRecord(**output)
            for role, output in data.get("role_outputs", {}).items()
        }
        delivery_status_by_role = {
            role: RoleDeliveryRecord(**delivery)
            for role, delivery in data.get("delivery_status_by_role", {}).items()
        }
        payload = dict(data)
        payload["role_outputs"] = role_outputs
        payload["delivery_status_by_role"] = delivery_status_by_role
        return cls(**payload)


class AutonomousStateStore:
    def __init__(
        self,
        state_dir: str | Path = AUTONOMOUS_STATE_DIR,
        frontend_export_path: str | Path | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.frontend_export_path = (
            Path(frontend_export_path) if frontend_export_path else None
        )

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
        if self.frontend_export_path:
            self.frontend_export_path.parent.mkdir(parents=True, exist_ok=True)
            self.frontend_export_path.write_text(
                json.dumps(
                    build_frontend_mission_control_export(state),
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

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


def build_frontend_mission_control_export(
    state: AutonomousRunState,
) -> dict[str, Any]:
    roles = [_frontend_role_status(state, role) for role in ROLE_ORDER]
    current_role = next(
        (
            role_status["display_name"]
            for role_status in roles
            if role_status["status"] in ("running", "failed", "waiting")
        ),
        (
            "Incident Commander Agent"
            if state.status == "complete"
            else "Alert Triage Agent"
        ),
    )

    return {
        "schema_version": 1,
        "source_state_file": ".workflow-legion-state/mission-control-status.json",
        "incident_id": state.incident_id,
        "run_id": state.run_id,
        "chain_status": state.status,
        "current_chain": (
            "Triage -> Threat Intel + Forensics -> Compliance -> "
            "Incident Commander -> stop"
        ),
        "current_role": current_role,
        "roles": roles,
        "provider_stack": _provider_stack_labels(),
        "final_commander_decision": {
            "status": _commander_decision_status(state),
            "summary": state.final_decision_state or "",
        },
        "band_proof_note": (
            "Band is the collaboration fabric and proof surface: agents coordinate "
            "through visible room messages, mentions, handoffs, shared context, and "
            "task state."
        ),
        "internal_queue_note": (
            "The backend deterministic runtime/state machine continues downstream "
            "execution through its internal handoff queue only after successful "
            "visible Band posts."
        ),
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }


def _frontend_role_status(
    state: AutonomousRunState,
    role: str,
) -> dict[str, Any]:
    definition = ROLE_DEFINITIONS[role]
    output = state.role_outputs.get(role)
    delivery = state.delivery_status_by_role.get(role)
    status = _status_for_role(state, role)

    return {
        "role": role,
        "display_name": definition.display_name,
        "status": status,
        "provider": output.provider_name if output else definition.provider_name,
        "provider_mode": output.provider_mode if output else "pending",
        "summary": output.summary if output else "",
        "handoff_targets": _handoff_target_display_names(
            output.handoff_roles if output else definition.handoff_targets
        ),
        "delivery": _safe_delivery_status(delivery),
        "completed_at": output.completed_at if output else None,
    }


def _status_for_role(state: AutonomousRunState, role: str) -> str:
    if role in state.role_outputs:
        return "complete"

    delivery = state.delivery_status_by_role.get(role)
    if delivery and not delivery.delivered:
        return "failed"

    if state.pending_role_message_ids.get(role):
        return "running" if _upstream_roles_complete(state, role) else "waiting"

    if state.completed_roles:
        return "waiting"

    return "waiting" if role == "triage" and state.status == "waiting" else "idle"


def _upstream_roles_complete(state: AutonomousRunState, role: str) -> bool:
    return all(upstream in state.completed_roles for upstream in UPSTREAM_ROLES[role])


def _safe_delivery_status(delivery: RoleDeliveryRecord | None) -> dict[str, Any]:
    if delivery is None:
        return {
            "status": "not_attempted",
            "delivered": False,
            "status_code": None,
            "attempted_at": None,
        }

    return {
        "status": delivery.status,
        "delivered": delivery.delivered,
        "status_code": delivery.status_code,
        "detail": delivery.detail,
        "attempted_at": delivery.attempted_at,
    }


def _handoff_target_display_names(targets: list[str] | tuple[str, ...]) -> list[str]:
    names: list[str] = []
    for target in targets:
        definition = ROLE_DEFINITIONS.get(target)
        if definition:
            names.append(definition.display_name)
    return names


def _safe_delivery_detail(detail: str | None) -> str | None:
    if not detail:
        return None

    redacted = re.sub(
        r"(?i)\b(api[_-]?key|token|authorization)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        str(detail),
    )
    redacted = re.sub(
        r"(?i)\bbearer\s+[A-Za-z0-9._\-/]+",
        "Bearer [REDACTED]",
        redacted,
    )
    return " ".join(redacted.split())[:240]


def _provider_stack_labels() -> list[dict[str, Any]]:
    stack: dict[str, list[str]] = {}
    for role in ROLE_ORDER:
        definition = ROLE_DEFINITIONS[role]
        stack.setdefault(definition.provider_name, []).append(definition.display_name)

    return [
        {
            "provider": provider,
            "roles": roles,
        }
        for provider, roles in stack.items()
    ]


def _commander_decision_status(state: AutonomousRunState) -> str:
    if "commander" in state.role_outputs:
        return "complete"
    delivery = state.delivery_status_by_role.get("commander")
    if delivery and not delivery.delivered:
        return "failed"
    return "pending"
