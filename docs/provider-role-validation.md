# AI/ML API Role Validation

Issue #53 validates provider-backed reasoning for the first three autonomous
task agents using the shared `WL-INC-001` incident context.

## Provider Selection

| Role | Provider | Model setting | Fallback |
| --- | --- | --- | --- |
| Triage | AI/ML API (`aimlapi`) | `AIML_MODEL` | `deterministic_fallback` |
| Threat Intel | AI/ML API (`aimlapi`) | `AIML_MODEL` | `deterministic_fallback` |
| Forensics | AI/ML API (`aimlapi`) | `AIML_MODEL` | `deterministic_fallback` |

The documented local model selection is `gpt-4o-mini`, as shown in
`.env.example`. The legacy `AIMLAPI_MODEL` alias remains supported. Provider
keys must exist only in an untracked local `.env`.

## Validation Command

From the repository root:

```bash
python backend/validate_provider_roles.py
```

The command evaluates role scope, evidence grounding, unsupported breach or
exfiltration claims, Band post length, and handoff mentions. It writes the
sanitized report to:

```text
.workflow-legion-state/provider-role-validation.md
```

That directory is gitignored. The report includes provider name, model, role,
provider mode, pass/fail checks, notes, and the safe Band post. It never reads
provider credentials into report fields.

To require a real AI/ML API response for all three roles:

```bash
python backend/validate_provider_roles.py --require-provider-live
```

The same check is available as an opt-in integration test:

```bash
RUN_LIVE_PROVIDER_TESTS=1 env/bin/python -m unittest discover -s tests -v
```

Normal test runs skip this networked integration test. This keeps the default
suite deterministic and free of provider billing or availability dependencies.

Without a local `AIML_API_KEY` and `AIML_MODEL`, each role must report
`deterministic_fallback`. A live response that is malformed, exceeds the Band
post limit, leaves its role, invents evidence, adds an unexpected handoff, or
makes a definitive unsupported breach/exfiltration claim is rejected and also
uses `deterministic_fallback`.

## Safety Boundary

Do not commit, paste, log, screenshot, or share provider keys, tokens, sponsor
codes, QR codes, redemption links, credentials, or `.env` contents. Only the
sanitized local validation report is appropriate for review.
