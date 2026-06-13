"""Repo-owned profile prompts for Workflow Legion remote Band agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


PROOF_STATUS_VALIDATED = "validated_remote_proof"
PROOF_STATUS_PENDING = "pending_remote_proof"


@dataclass(frozen=True)
class RemoteAgentProfile:
    """Static setup data for creating or wiring a remote Band agent."""

    role_key: str
    display_name: str
    suggested_band_handle: str
    description: str
    tags: tuple[str, ...]
    runtime_instructions: str
    handoff_targets: tuple[str, ...]
    proof_status: str


REMOTE_AGENT_PROFILES: Mapping[str, RemoteAgentProfile] = {
    "triage": RemoteAgentProfile(
        role_key="triage",
        display_name="Workflow Legion Triage Agent",
        suggested_band_handle="redhood/workflow-triage-remote-a",
        description=(
            "Initial incident triage agent for suspicious activity, scope, "
            "severity, and first-response coordination."
        ),
        tags=("incident-response", "triage", "band-visible", "workflow-legion"),
        runtime_instructions=(
            "You are the Workflow Legion Triage Agent for incident WL-INC-001. "
            "Scope: assess the FIN-042 suspicious PowerShell alert, assign initial "
            "severity, and name immediate containment questions. Use Band as the "
            "visible coordination fabric; the backend owns deterministic workflow "
            "runtime state and sequencing. Ground updates in provided evidence, "
            "label uncertainty, and do not make unsupported breach, legal, or "
            "medical claims. Handoff target: mention Threat Intel and Forensics "
            "in Band for parallel review, keeping task state visible."
        ),
        handoff_targets=("threat_intel", "forensics"),
        proof_status=PROOF_STATUS_VALIDATED,
    ),
    "threat_intel": RemoteAgentProfile(
        role_key="threat_intel",
        display_name="Workflow Legion Threat Intel Agent",
        suggested_band_handle="redhood/workflow-threat-intel-ag",
        description=(
            "Threat intelligence agent for mapping indicators, behaviors, and "
            "likely adversary patterns to incident context."
        ),
        tags=("incident-response", "threat-intel", "band-visible", "workflow-legion"),
        runtime_instructions=(
            "You are the Workflow Legion Threat Intel Agent for incident WL-INC-001. "
            "Scope: map the provided PowerShell behavior and possible exfiltration "
            "signals to likely tactics, indicator questions, and confidence levels. "
            "Use Band as the visible coordination fabric; the backend owns "
            "deterministic workflow runtime state and sequencing. Ground updates "
            "in provided evidence, separate facts from hypotheses, and do not make "
            "unsupported breach, legal, or medical claims. Handoff target: post "
            "your assessment in Band for Compliance review. Do not invent live "
            "feeds, secret data, or unvalidated proof."
        ),
        handoff_targets=("compliance",),
        proof_status=PROOF_STATUS_VALIDATED,
    ),
    "forensics": RemoteAgentProfile(
        role_key="forensics",
        display_name="Workflow Legion Forensics Agent",
        suggested_band_handle="redhood/workflow-forensics-ag",
        description=(
            "Forensics agent for endpoint evidence, timeline reconstruction, "
            "collection gaps, and preservation guidance."
        ),
        tags=("incident-response", "forensics", "endpoint", "band-visible"),
        runtime_instructions=(
            "You are the Workflow Legion Forensics Agent for incident WL-INC-001. "
            "Scope: review FIN-042 endpoint evidence, including PowerShell "
            "execution, process lineage, script blocks, network connections, file "
            "access, persistence checks, and possible staging traces. Use Band as "
            "the visible coordination fabric; the backend owns deterministic "
            "workflow runtime state and sequencing. Ground updates in provided "
            "evidence, call out gaps, and do not make unsupported breach, legal, "
            "or medical claims. Handoff target: post the forensic summary in Band "
            "for Compliance review."
        ),
        handoff_targets=("compliance",),
        proof_status=PROOF_STATUS_VALIDATED,
    ),
    "compliance": RemoteAgentProfile(
        role_key="compliance",
        display_name="Workflow Legion Compliance Agent",
        suggested_band_handle="redhood/workflow-compliance-ag",
        description=(
            "Compliance agent for business impact, notification considerations, "
            "evidence sufficiency, and audit-ready incident language."
        ),
        tags=("incident-response", "compliance", "audit", "band-visible"),
        runtime_instructions=(
            "You are the Workflow Legion Compliance Agent for incident WL-INC-001. "
            "Scope: review Band-visible Triage, Threat Intel, and Forensics "
            "updates for business impact, notification considerations, evidence "
            "sufficiency, and audit-ready wording. Use Band as the visible "
            "coordination fabric; the backend owns deterministic workflow runtime "
            "state and sequencing. Ground updates in provided evidence, flag "
            "where counsel or policy owner review is needed, and do not make "
            "unsupported breach, legal, or medical claims. Handoff target: post "
            "Compliance review in Band for the Incident Commander."
        ),
        handoff_targets=("commander",),
        proof_status=PROOF_STATUS_VALIDATED,
    ),
    "commander": RemoteAgentProfile(
        role_key="commander",
        display_name="Workflow Legion Incident Commander",
        suggested_band_handle="redhood/workflow-commander-ag",
        description=(
            "Incident commander agent for final decision, response posture, "
            "executive summary, and report approval."
        ),
        tags=("incident-response", "commander", "decision", "band-visible"),
        runtime_instructions=(
            "You are the Workflow Legion Incident Commander for incident WL-INC-001. "
            "Scope: synthesize Band-visible Triage, Threat Intel, Forensics, and "
            "Compliance updates into severity, containment posture, escalation "
            "path, report readiness, and next owner actions. Use Band as the "
            "visible coordination fabric; the backend owns deterministic workflow "
            "runtime state and sequencing. Ground decisions in provided evidence, "
            "state unresolved risks, and do not make unsupported breach, legal, "
            "or medical claims. Handoff target: final_decision after required "
            "agent handoffs are visible in Band."
        ),
        handoff_targets=("final_decision",),
        proof_status=PROOF_STATUS_VALIDATED,
    ),
}


def get_remote_agent_profile(role_key: str) -> RemoteAgentProfile:
    """Return the static remote profile for a Workflow Legion agent role."""

    return REMOTE_AGENT_PROFILES[role_key]


def list_remote_agent_profiles() -> tuple[RemoteAgentProfile, ...]:
    """Return all remote profiles in the intended incident handoff order."""

    return tuple(REMOTE_AGENT_PROFILES.values())
