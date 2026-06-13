from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.core.settings import Settings, settings
from app.models.incident import IncidentState
from app.services.deterministic_agents import (
    build_commander_finding,
    build_compliance_finding,
    build_forensics_finding,
    build_threat_intel_finding,
    build_triage_finding,
)
from app.services.llm_provider_router import ProviderConfig


ROLE_ORDER = ("triage", "threat_intel", "forensics", "compliance", "commander")
UPSTREAM_ROLES = {
    "triage": (),
    "threat_intel": ("triage",),
    "forensics": ("triage",),
    "compliance": ("threat_intel", "forensics"),
    "commander": ("compliance",),
}


@dataclass(frozen=True)
class RoleDefinition:
    role: str
    display_name: str
    trigger_criteria: str
    role_scope: str
    provider_name: str
    handoff_targets: tuple[str, ...]
    stop_condition: str | None = None


@dataclass(frozen=True)
class AutonomousRoleContext:
    incident: IncidentState
    run_id: str
    source_message_ids: tuple[str, ...]
    upstream_summaries: dict[str, str]
    handles_by_role: dict[str, str]


@dataclass(frozen=True)
class AutonomousRoleOutput:
    role: str
    provider_name: str
    provider_mode: str
    summary: str
    evidence: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    handoff_roles: tuple[str, ...]
    band_message: str


class ReasoningProvider(Protocol):
    async def decide(
        self,
        definition: RoleDefinition,
        context: AutonomousRoleContext,
    ) -> AutonomousRoleOutput:
        ...


ROLE_DEFINITIONS: dict[str, RoleDefinition] = {
    "triage": RoleDefinition(
        role="triage",
        display_name="Alert Triage Agent",
        trigger_criteria="Band mention plus AUTO:START for the incident ID.",
        role_scope=(
            "Classify WL-INC-001, cite the triggering alert evidence, and request "
            "parallel Threat Intel and Forensics work."
        ),
        provider_name="aimlapi",
        handoff_targets=("threat_intel", "forensics"),
    ),
    "threat_intel": RoleDefinition(
        role="threat_intel",
        display_name="Threat Intel Agent",
        trigger_criteria="Band mention from Triage output for the active run.",
        role_scope=(
            "Enrich IOCs from the incident record and hand governance concerns to "
            "Compliance."
        ),
        provider_name="aimlapi",
        handoff_targets=("compliance",),
    ),
    "forensics": RoleDefinition(
        role="forensics",
        display_name="Forensics Agent",
        trigger_criteria="Band mention from Triage output for the active run.",
        role_scope=(
            "Build the evidence timeline from endpoint, identity, file, and network "
            "signals, then hand risk context to Compliance."
        ),
        provider_name="aimlapi",
        handoff_targets=("compliance",),
    ),
    "compliance": RoleDefinition(
        role="compliance",
        display_name="Compliance Agent",
        trigger_criteria=(
            "Band mention from Threat Intel or Forensics once both upstream roles "
            "have completed for the run."
        ),
        role_scope=(
            "Deduplicate upstream handoffs, review audit/escalation risk, and ask "
            "the Incident Commander for a decision."
        ),
        provider_name="featherless",
        handoff_targets=("commander",),
    ),
    "commander": RoleDefinition(
        role="commander",
        display_name="Incident Commander Agent",
        trigger_criteria="Band mention from Compliance output for the active run.",
        role_scope=(
            "Synthesize visible role outputs and issue the final containment "
            "decision."
        ),
        provider_name="featherless",
        handoff_targets=(),
        stop_condition="Post final containment decision for WL-INC-001.",
    ),
}


class AutonomousReasoningProvider:
    def __init__(
        self,
        provider_mode: str = "auto",
        settings_obj: Settings = settings,
    ) -> None:
        self.provider_mode = provider_mode.strip().lower() or "auto"
        self.settings = settings_obj

    async def decide(
        self,
        definition: RoleDefinition,
        context: AutonomousRoleContext,
    ) -> AutonomousRoleOutput:
        deterministic_output = build_deterministic_role_output(definition, context)

        if self.provider_mode == "deterministic":
            return deterministic_output

        provider_config = _provider_config_for_role(definition, self.settings)

        if not provider_config.api_key or not provider_config.model:
            return deterministic_output

        try:
            return await self._call_openai_compatible_provider(
                provider_config,
                definition,
                context,
                deterministic_output,
            )
        except Exception:
            return deterministic_output

    async def _call_openai_compatible_provider(
        self,
        provider_config: ProviderConfig,
        definition: RoleDefinition,
        context: AutonomousRoleContext,
        fallback_output: AutonomousRoleOutput,
    ) -> AutonomousRoleOutput:
        prompt = _build_provider_prompt(definition, context, fallback_output)
        payload = {
            "model": provider_config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a bounded cyber incident task agent. Return only "
                        "compact JSON with keys summary, evidence, "
                        "recommended_actions, and band_message. Ground every claim "
                        "in the supplied incident evidence."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {provider_config.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{provider_config.base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )

        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = _extract_json_object(content)

        return AutonomousRoleOutput(
            role=definition.role,
            provider_name=provider_config.name,
            provider_mode="provider_live",
            summary=str(parsed.get("summary") or fallback_output.summary),
            evidence=tuple(
                str(item)
                for item in parsed.get("evidence", fallback_output.evidence)
            ),
            recommended_actions=tuple(
                str(item)
                for item in parsed.get(
                    "recommended_actions",
                    fallback_output.recommended_actions,
                )
            ),
            handoff_roles=definition.handoff_targets,
            band_message=_ensure_run_marker_and_mentions(
                str(parsed.get("band_message") or fallback_output.band_message),
                definition,
                context,
            ),
        )


def build_deterministic_role_output(
    definition: RoleDefinition,
    context: AutonomousRoleContext,
) -> AutonomousRoleOutput:
    finding = _build_deterministic_finding(definition.role, context)
    evidence = tuple(
        f"{item.evidence_id}: {item.summary} Source: {item.source}."
        for item in finding.evidence
    )
    if finding.timeline:
        evidence = evidence + tuple(
            f"{event.time}: {event.actor} {event.action}. {event.significance}"
            for event in finding.timeline
        )

    message = _ensure_run_marker_and_mentions(
        finding.band_message,
        definition,
        context,
    )

    return AutonomousRoleOutput(
        role=definition.role,
        provider_name=definition.provider_name,
        provider_mode="deterministic_fallback",
        summary=finding.summary,
        evidence=evidence,
        recommended_actions=tuple(finding.recommended_actions),
        handoff_roles=definition.handoff_targets,
        band_message=message,
    )


def _build_deterministic_finding(role: str, context: AutonomousRoleContext):
    incident = context.incident
    handles = context.handles_by_role

    if role == "triage":
        return build_triage_finding(
            incident,
            threat_handle=handles["threat_intel"],
            forensics_handle=handles["forensics"],
        )
    if role == "threat_intel":
        return build_threat_intel_finding(
            incident,
            compliance_handle=handles["compliance"],
        )
    if role == "forensics":
        return build_forensics_finding(
            incident,
            compliance_handle=handles["compliance"],
        )
    if role == "compliance":
        return build_compliance_finding(
            incident,
            commander_handle=handles["commander"],
        )
    if role == "commander":
        return build_commander_finding(incident)

    raise ValueError(f"Unknown autonomous role: {role}")


def _provider_config_for_role(
    definition: RoleDefinition,
    settings_obj: Settings,
) -> ProviderConfig:
    provider_name = "aimlapi" if definition.provider_name == "aiml" else definition.provider_name

    if provider_name == "featherless":
        return ProviderConfig(
            name="featherless",
            api_key=settings_obj.featherless_api_key,
            base_url=settings_obj.featherless_base_url,
            model=settings_obj.featherless_model,
        )

    if provider_name == "aimlapi":
        return ProviderConfig(
            name="aimlapi",
            api_key=settings_obj.aiml_api_key or settings_obj.aimlapi_api_key,
            base_url=settings_obj.aiml_base_url or settings_obj.aimlapi_base_url,
            model=settings_obj.aiml_model or settings_obj.aimlapi_model,
        )

    return ProviderConfig(name=provider_name, api_key=None)


def _build_provider_prompt(
    definition: RoleDefinition,
    context: AutonomousRoleContext,
    fallback_output: AutonomousRoleOutput,
) -> str:
    incident = context.incident
    upstream = "\n".join(
        f"- {role}: {summary}"
        for role, summary in sorted(context.upstream_summaries.items())
    )
    return (
        f"Incident: {incident.incident_id}\n"
        f"Host: {incident.affected_host}\n"
        f"User: {incident.affected_user}\n"
        f"Department: {incident.department}\n"
        f"Summary: {incident.summary}\n"
        f"Indicators: {json.dumps(incident.indicators, sort_keys=True)}\n"
        f"Role: {definition.display_name}\n"
        f"Scope: {definition.role_scope}\n"
        f"Handoff targets: {', '.join(definition.handoff_targets) or 'none'}\n"
        f"Run marker must be included: "
        f"[WL-AUTO:{incident.incident_id}:{definition.role}:{context.run_id}]\n"
        f"Upstream context:\n{upstream or '- none'}\n"
        f"Deterministic baseline:\n{fallback_output.summary}\n"
    )


def _extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Provider did not return a JSON object.")

    return json.loads(stripped[start : end + 1])


def _ensure_run_marker_and_mentions(
    message: str,
    definition: RoleDefinition,
    context: AutonomousRoleContext,
) -> str:
    marker = f"[WL-AUTO:{context.incident.incident_id}:{definition.role}:{context.run_id}]"
    cleaned = message.strip()
    if marker not in cleaned:
        cleaned = f"{marker} {cleaned}"

    for role in reversed(definition.handoff_targets):
        handle = context.handles_by_role[role].strip().removeprefix("@")
        mention = f"@{handle}"
        if mention.lower() not in cleaned.lower():
            cleaned = f"{mention} {cleaned}"

    return cleaned
