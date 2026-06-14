import asyncio
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.settings import Settings  # noqa: E402
from app.services.autonomous_role_agents import (  # noqa: E402
    PROVIDER_VALIDATION_ROLES,
    ROLE_DEFINITIONS,
    AutonomousReasoningProvider,
    AutonomousRoleContext,
    _build_provider_prompt,
    _provider_config_for_role,
    build_deterministic_role_output,
)
from app.services.band_agent_registry import (  # noqa: E402
    build_band_remote_agent_registry,
)
from app.services.incident_repository import build_demo_incident  # noqa: E402
from app.services.provider_role_validation import (  # noqa: E402
    evaluate_provider_role_output,
    render_provider_role_validation_report,
)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self._content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": self._content,
                    }
                }
            ]
        }


class _FakeAsyncClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.request_url = None
        self.request_headers = None
        self.request_payload = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url: str, headers: dict, json: dict) -> _FakeResponse:
        self.request_url = url
        self.request_headers = headers
        self.request_payload = json
        return _FakeResponse(self.content)


class ProviderRoleValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            aiml_api_key="local-test-key",
            aiml_model="gpt-4o-mini",
            aimlapi_api_key=None,
            aimlapi_model=None,
            band_triage_handle="Triage",
            band_threat_intel_handle="ThreatIntel",
            band_forensics_handle="Forensics",
            band_compliance_handle="Compliance",
            band_commander_handle="Commander",
        )
        self.incident = build_demo_incident()
        registry = build_band_remote_agent_registry(self.settings)
        self.handles = {
            role: agent.handle for role, agent in registry.items()
        }

    def test_first_three_roles_select_aimlapi_and_configured_model(self) -> None:
        for role in PROVIDER_VALIDATION_ROLES:
            config = _provider_config_for_role(
                ROLE_DEFINITIONS[role],
                self.settings,
            )
            self.assertEqual(config.name, "aimlapi")
            self.assertEqual(config.model, "gpt-4o-mini")

    def test_provider_prompt_includes_issue_53_safety_constraints(self) -> None:
        for role in PROVIDER_VALIDATION_ROLES:
            definition = ROLE_DEFINITIONS[role]
            context = self._context(role)
            fallback = build_deterministic_role_output(definition, context)

            prompt = _build_provider_prompt(definition, context, fallback)

            self.assertIn("Stay inside the assigned role", prompt)
            self.assertIn("unconfirmed possibilities", prompt)
            self.assertIn("Keep band_message at or below 600 characters", prompt)
            self.assertIn("Make the Band handoff explicit", prompt)
            self.assertIn("Deterministic baseline evidence", prompt)

    def test_all_three_roles_fall_back_without_provider_credentials(self) -> None:
        settings_without_key = Settings(
            aiml_api_key=None,
            aimlapi_api_key=None,
            aiml_model="gpt-4o-mini",
            band_triage_handle="Triage",
            band_threat_intel_handle="ThreatIntel",
            band_forensics_handle="Forensics",
            band_compliance_handle="Compliance",
            band_commander_handle="Commander",
        )
        registry = build_band_remote_agent_registry(settings_without_key)
        handles = {role: agent.handle for role, agent in registry.items()}
        provider = AutonomousReasoningProvider(
            provider_mode="auto",
            settings_obj=settings_without_key,
        )

        for role in PROVIDER_VALIDATION_ROLES:
            context = AutonomousRoleContext(
                incident=self.incident,
                run_id="fallback-test",
                source_message_ids=("m1",),
                upstream_summaries={},
                handles_by_role=handles,
            )
            output = asyncio.run(
                provider.decide(ROLE_DEFINITIONS[role], context)
            )

            self.assertEqual(output.provider_name, "aimlapi")
            self.assertEqual(output.provider_mode, "deterministic_fallback")

    def test_safe_provider_outputs_pass_for_all_three_roles(self) -> None:
        provider = AutonomousReasoningProvider(
            provider_mode="auto",
            settings_obj=self.settings,
        )
        outputs = {}

        for role in PROVIDER_VALIDATION_ROLES:
            context = self._context(
                role,
                upstream_summaries={
                    "triage": outputs["triage"].summary
                }
                if role != "triage"
                else {},
            )
            fake_client = _FakeAsyncClient(
                json.dumps(self._safe_provider_payload(role))
            )
            with patch(
                "app.services.autonomous_role_agents.httpx.AsyncClient",
                return_value=fake_client,
            ):
                output = asyncio.run(
                    provider.decide(ROLE_DEFINITIONS[role], context)
                )

            result = evaluate_provider_role_output(
                output,
                ROLE_DEFINITIONS[role],
                context,
                "gpt-4o-mini",
            )
            outputs[role] = output

            self.assertEqual(output.provider_mode, "provider_live")
            self.assertEqual(result.output_quality, "pass")
            self.assertTrue(result.stayed_in_role)
            self.assertTrue(result.evidence_grounded)
            self.assertTrue(result.safe_for_band_runtime)
            self.assertTrue(result.clean_handoff_target)
            self.assertNotIn(
                "local-test-key",
                json.dumps(fake_client.request_payload),
            )

    def test_unsupported_provider_claim_uses_deterministic_fallback(self) -> None:
        role = "triage"
        context = self._context(role)
        payload = self._safe_provider_payload(role)
        payload["summary"] = "Confirmed exfiltration from FIN-042."
        payload["band_message"] = (
            "Confirmed exfiltration from FIN-042. Escalating the breach."
        )
        fake_client = _FakeAsyncClient(json.dumps(payload))
        provider = AutonomousReasoningProvider(
            provider_mode="auto",
            settings_obj=self.settings,
        )

        with patch(
            "app.services.autonomous_role_agents.httpx.AsyncClient",
            return_value=fake_client,
        ):
            output = asyncio.run(
                provider.decide(ROLE_DEFINITIONS[role], context)
            )

        self.assertEqual(output.provider_mode, "deterministic_fallback")
        self.assertNotIn("Confirmed exfiltration", output.summary)

    def test_conditional_exfiltration_language_is_not_treated_as_confirmation(
        self,
    ) -> None:
        role = "triage"
        context = self._context(role)
        output = build_deterministic_role_output(
            ROLE_DEFINITIONS[role],
            context,
        )

        result = evaluate_provider_role_output(
            output,
            ROLE_DEFINITIONS[role],
            context,
            "gpt-4o-mini",
        )

        self.assertEqual(result.output_quality, "pass")
        self.assertTrue(result.evidence_grounded)
        self.assertTrue(result.safe_for_band_runtime)

    def test_report_contains_no_provider_credential(self) -> None:
        role = "triage"
        context = self._context(role)
        output = build_deterministic_role_output(
            ROLE_DEFINITIONS[role],
            context,
        )
        result = evaluate_provider_role_output(
            output,
            ROLE_DEFINITIONS[role],
            context,
            "gpt-4o-mini",
        )

        report = render_provider_role_validation_report(
            [result],
            self.incident.incident_id,
            generated_at=datetime(2026, 6, 14, tzinfo=timezone.utc),
        )

        self.assertNotIn(self.settings.aiml_api_key, report)
        self.assertNotIn("AIML_API_KEY=", report)
        self.assertNotIn("api_key", report.lower())

    def _context(
        self,
        role: str,
        upstream_summaries: dict[str, str] | None = None,
    ) -> AutonomousRoleContext:
        return AutonomousRoleContext(
            incident=self.incident,
            run_id="provider-test",
            source_message_ids=(f"m-{role}",),
            upstream_summaries=upstream_summaries or {},
            handles_by_role=self.handles,
        )

    def _safe_provider_payload(self, role: str) -> dict:
        payloads = {
            "triage": {
                "summary": (
                    "Triage rates the FIN-042 PowerShell alert high severity; "
                    "possible exfiltration remains unconfirmed."
                ),
                "evidence": [
                    "FIN-042 executed powershell.exe.",
                    "Outbound traffic followed sensitive file access.",
                ],
                "recommended_actions": [
                    "Preserve FIN-042 telemetry.",
                    "Request parallel IOC and forensic review.",
                ],
                "band_message": (
                    "WL-INC-001 triage: FIN-042 PowerShell activity is high risk; "
                    "possible exfiltration is unconfirmed. Review IOCs and timeline."
                ),
            },
            "threat_intel": {
                "summary": (
                    "Threat Intel finds destination 185.199.108.153 suspicious "
                    "by context, not proof of malicious activity."
                ),
                "evidence": [
                    "FIN-042 connected to 185.199.108.153 after PowerShell activity.",
                    "invoice_update.exe is an indicator requiring sandbox review.",
                ],
                "recommended_actions": [
                    "Monitor or block 185.199.108.153 during investigation.",
                    "Submit invoice_update.exe for controlled analysis.",
                ],
                "band_message": (
                    "WL-INC-001 Threat Intel: IOCs are suspicious by context only. "
                    "Compliance should review the finance-data risk."
                ),
            },
            "forensics": {
                "summary": (
                    "Forensics reconstructs PowerShell execution, finance file "
                    "access, and later outbound traffic on FIN-042."
                ),
                "evidence": [
                    "powershell.exe launched invoice_update.exe on FIN-042.",
                    "finance_q4_forecast.xlsx was accessed before outbound traffic.",
                ],
                "recommended_actions": [
                    "Preserve FIN-042 endpoint and proxy evidence.",
                    "Review j.morgan sessions.",
                ],
                "band_message": (
                    "WL-INC-001 Forensics: the FIN-042 timeline is high risk, but "
                    "data exfiltration remains unconfirmed. Compliance review needed."
                ),
            },
        }
        return payloads[role]


if __name__ == "__main__":
    unittest.main()
