from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.services.autonomous_role_agents import (
    AutonomousRoleContext,
    AutonomousRoleOutput,
    RoleDefinition,
    output_has_clean_handoff,
    output_has_unsupported_claim,
    output_is_evidence_grounded,
    output_is_safe_for_band,
    output_stays_in_role,
    provider_output_safety_issues,
)


@dataclass(frozen=True)
class ProviderRoleValidationResult:
    provider: str
    model: str
    role: str
    provider_mode: str
    output_quality: str
    stayed_in_role: bool
    evidence_grounded: bool
    safe_for_band_runtime: bool
    clean_handoff_target: bool
    notes: tuple[str, ...]
    band_post: str


def evaluate_provider_role_output(
    output: AutonomousRoleOutput,
    definition: RoleDefinition,
    context: AutonomousRoleContext,
    model: str | None,
) -> ProviderRoleValidationResult:
    stayed_in_role = output_stays_in_role(output, definition)
    evidence_grounded = (
        output_is_evidence_grounded(output, context)
        and not output_has_unsupported_claim(output)
    )
    safe_for_band_runtime = output_is_safe_for_band(
        output,
        definition,
        context,
    )
    clean_handoff_target = output_has_clean_handoff(
        output,
        definition,
        context,
    )
    checks = (
        stayed_in_role,
        evidence_grounded,
        safe_for_band_runtime,
        clean_handoff_target,
    )

    notes = list(provider_output_safety_issues(output, definition, context))
    if output.provider_mode == "deterministic_fallback":
        notes.insert(
            0,
            "Provider credentials/model were unavailable or the provider response "
            "failed safety validation; deterministic fallback was evaluated.",
        )
    elif all(checks):
        notes.append("Provider-backed output passed the automated role checks.")

    return ProviderRoleValidationResult(
        provider=output.provider_name,
        model=model or "not configured",
        role=definition.display_name,
        provider_mode=output.provider_mode,
        output_quality="pass" if all(checks) else "review required",
        stayed_in_role=stayed_in_role,
        evidence_grounded=evidence_grounded,
        safe_for_band_runtime=safe_for_band_runtime,
        clean_handoff_target=clean_handoff_target,
        notes=tuple(notes) or ("No validation notes.",),
        band_post=output.band_message,
    )


def render_provider_role_validation_report(
    results: list[ProviderRoleValidationResult],
    incident_id: str,
    generated_at: datetime | None = None,
) -> str:
    timestamp = generated_at or datetime.now(timezone.utc)
    lines = [
        "# AI/ML API Role Validation",
        "",
        f"Generated: {timestamp.isoformat()}",
        f"Incident: {incident_id}",
        "",
        "This report contains provider metadata and task-agent output only. "
        "It never includes provider credentials or local `.env` contents.",
    ]

    for result in results:
        lines.extend(
            (
                "",
                f"## {result.role}",
                "",
                f"Provider: {result.provider}",
                f"Model: {result.model}",
                f"Provider mode: {result.provider_mode}",
                f"Output quality: {result.output_quality}",
                f"Stayed in role: {_yes_no(result.stayed_in_role)}",
                f"Evidence-grounded: {_yes_no(result.evidence_grounded)}",
                f"Safe for Band runtime: {_yes_no(result.safe_for_band_runtime)}",
                f"Clean handoff target: {_yes_no(result.clean_handoff_target)}",
                f"Notes: {' '.join(result.notes)}",
                f"Band post: {result.band_post}",
            )
        )

    lines.append("")
    return "\n".join(lines)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
