from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys
from typing import Sequence


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import settings  # noqa: E402
from app.services.autonomous_role_agents import (  # noqa: E402
    PROVIDER_VALIDATION_ROLES,
    ROLE_DEFINITIONS,
    UPSTREAM_ROLES,
    AutonomousReasoningProvider,
    AutonomousRoleContext,
    _provider_config_for_role,
)
from app.services.band_agent_registry import (  # noqa: E402
    build_band_remote_agent_registry,
)
from app.services.incident_repository import build_demo_incident  # noqa: E402
from app.services.provider_role_validation import (  # noqa: E402
    ProviderRoleValidationResult,
    evaluate_provider_role_output,
    render_provider_role_validation_report,
)


DEFAULT_REPORT_PATH = (
    Path(".workflow-legion-state") / "provider-role-validation.md"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate AI/ML API reasoning for the WL-INC-001 Triage, "
            "Threat Intel, and Forensics roles."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Local Markdown report path. The default directory is gitignored.",
    )
    parser.add_argument(
        "--provider-mode",
        choices=("auto", "deterministic"),
        default=None,
        help=(
            "Override AUTONOMOUS_AGENT_PROVIDER_MODE. Auto uses AI/ML API when "
            "a local key and model are configured."
        ),
    )
    parser.add_argument(
        "--require-provider-live",
        action="store_true",
        help="Return a non-zero status unless all three roles used provider_live.",
    )
    return parser.parse_args(argv)


async def run_validation(
    provider_mode: str | None = None,
) -> list[ProviderRoleValidationResult]:
    incident = build_demo_incident()
    registry = build_band_remote_agent_registry(settings)
    handles = {role: agent.handle for role, agent in registry.items()}
    provider = AutonomousReasoningProvider(
        provider_mode=provider_mode or settings.autonomous_agent_provider_mode,
        settings_obj=settings,
    )
    outputs = {}
    results = []

    for role in PROVIDER_VALIDATION_ROLES:
        definition = ROLE_DEFINITIONS[role]
        context = AutonomousRoleContext(
            incident=incident,
            run_id="issue-53-validation",
            source_message_ids=(f"issue-53-{role}",),
            upstream_summaries={
                upstream_role: outputs[upstream_role].summary
                for upstream_role in UPSTREAM_ROLES[role]
                if upstream_role in outputs
            },
            handles_by_role=handles,
        )
        output = await provider.decide(definition, context)
        outputs[role] = output
        provider_config = _provider_config_for_role(definition, settings)
        results.append(
            evaluate_provider_role_output(
                output,
                definition,
                context,
                provider_config.model,
            )
        )

    return results


async def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    results = await run_validation(args.provider_mode)
    report = render_provider_role_validation_report(results, "WL-INC-001")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")

    print(f"Provider role validation report: {args.output}")
    for result in results:
        print(
            f"{result.role}: {result.output_quality} "
            f"({result.provider}/{result.model}, {result.provider_mode})"
        )

    if args.require_provider_live and any(
        result.provider_mode != "provider_live" for result in results
    ):
        print(
            "Provider-live validation incomplete. Configure AIML_API_KEY and "
            "AIML_MODEL locally, then rerun."
        )
        return 1

    return 0 if all(result.output_quality == "pass" for result in results) else 1


def run_cli(argv: Sequence[str] | None = None) -> int:
    try:
        return asyncio.run(main(argv))
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Provider role validation stopped by operator.")
        return 130


if __name__ == "__main__":
    raise SystemExit(run_cli())
