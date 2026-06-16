# Regulated Workflow Audit-Trail Evidence Packet

## Purpose

This packet helps judges review traceability for Workflow Legion as a regulated/high-stakes workflow demo. It summarizes what evidence to show, what each role contributes, and where the validated proof boundary starts and stops.

Use `WL-INC-003` as the recommended judge demo scenario because it has existing Band-visible and Mission Control supporting screenshots in `docs/screenshots/`.

## Validated Proof Boundary

The current validated proof is the hosted five-agent Band-triggered workflow running through Railway and Band:

```text
Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander -> stop
```

Band is the live collaboration fabric and proof surface. The Railway backend executes deterministic workflow/runtime logic and exports sanitized Mission Control status. AI/ML API and Featherless are optional provider support layers. Native.Builder/NativelyAI informed showcase and productization only.

This packet does not claim Agent-in-the-Loop observer proof, autonomous production incident response, or open-ended incident automation.

## Evidence Packet Fields

| Field | Judge-facing value |
| --- | --- |
| Incident ID | `WL-INC-003` |
| Scenario | Vendor invoice fraud / BEC workflow scenario |
| Run source | Human judge/operator posts a supported Band trigger |
| Trigger surface | Band room message mentioning the Triage remote agent |
| Runtime | Railway-hosted backend deterministic workflow/runtime logic |
| Handoff chain | `Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander -> stop` |
| Provider mode/labels | Informational only; provider fallback preserves workflow integrity |
| Band-visible proof | Five role-specific agent posts visible in Band |
| Mission Control state | Sanitized hosted completion status only |
| Final Commander decision | Terminal Commander post summarizes decision, containment recommendation, unresolved risk, and next owner actions |
| Stop condition | Commander is terminal; no downstream handoff follows |
| Validation commands | `python -m unittest discover -s tests -v`, `git diff --check`, secret-string grep, and `git status -sb` |

## Example Evidence Packet for WL-INC-003

| Field | Example value |
| --- | --- |
| Incident ID | `WL-INC-003` |
| Scenario | Vendor invoice fraud / BEC |
| Runtime-generated run id | `<runtime-generated run id>` |
| Band-visible message timestamp | `<Band-visible message timestamp>` |
| Mission Control status timestamp | `<Mission Control status timestamp>` |
| Run source | Human judge/operator Band trigger |
| Trigger surface | Band room message: `@Workflow Triage Remote Agent AUTO:START WL-INC-003` |
| Runtime | Railway-hosted backend |
| Handoff chain | `Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander -> stop` |
| Provider/status labels | Runtime-specific informational labels; deterministic fallback is acceptable when shown |
| Band-visible proof | Optional supporting screenshot if reviewed and still current: `docs/screenshots/proof_5_agents_in_chat_003_app.band.png` |
| Mission Control state | Optional supporting screenshot if reviewed and still current: `docs/screenshots/proof_completion_003_invoice_fraud_frontend_railway.app.png` |
| Commander decision | Commander posts the final operational decision in Band |
| Stop condition | Runtime stops after Commander; no downstream handoff follows |

## Handoff Chain

```text
Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander -> stop
```

Triage opens the incident, frames severity/context, and routes parallel work to Threat Intel and Forensics. Threat Intel and Forensics contribute their role outputs, then hand off to Compliance. Compliance reviews escalation/governance posture and hands off to Incident Commander. Incident Commander posts the final decision and ends the workflow.

## Role Output Checklist

| Role | Expected contribution |
| --- | --- |
| Triage | Incident frame, routing, initial severity/context |
| Threat Intel | Indicator and business-risk enrichment |
| Forensics | Evidence timeline and investigation gaps |
| Compliance | Escalation, governance, and audit wording |
| Incident Commander | Final decision, containment recommendation, and stop condition |

## Provider/Status Labels

Provider labels are informational only. AI/ML API and Featherless can support role reasoning experiments, but the validated workflow does not depend on a provider being live. If a provider is unavailable or a response fails validation, deterministic fallback preserves workflow integrity and keeps the demo replayable.

## Band-Visible Proof

Band room messages are the primary collaboration proof surface. Judges should see role-specific posts, mentions, handoffs, shared context, and the terminal Commander post in Band.

Do not replace Band-visible proof with a hidden backend-only trace.

## Mission Control State

Mission Control shows sanitized hosted completion status only. It is useful for judge visibility, but it is not the collaboration source of truth and must not expose private IDs, credentials, raw payloads, or local operator artifacts.

## Commander Decision and Stop Condition

Incident Commander is terminal. The Commander post should synthesize the Band-visible work, identify unresolved risk, recommend containment/escalation posture, and state that the workflow stops. No downstream handoff follows Commander.

## Validation Commands

Run these from the repository root:

```bash
python -m unittest discover -s tests -v
git diff --check
git grep --untracked -n -i "BAND_AGENT_KEY\|BAND_RECEIVE_KEY\|AIML_API_KEY\|AIMLAPI_API_KEY\|FEATHERLESS_API_KEY\|sponsor code\|redemption\|qr code\|private key\|secret" -- .
git status -sb
```

Only add the frontend build check if README/frontend files are touched beyond a docs pointer:

```bash
cd frontend-showcase
npm run build
cd ..
```

## What Not To Include

- `.env`
- API keys
- Band IDs
- room IDs
- chat IDs
- sponsor codes
- QR codes
- redemption links
- private credentials
- raw runtime proof JSON
- build output
- `node_modules`
- private screenshots
