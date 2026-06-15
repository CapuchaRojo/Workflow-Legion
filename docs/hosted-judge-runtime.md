# Hosted Judge Runtime

The hosted judge runtime is a thin FastAPI entrypoint around the existing
autonomous Band listener. It does not replace the architecture:

- Band remains the visible coordination fabric and proof surface.
- The backend executes deterministic runtime/state-machine logic.
- Mission Control exposes sanitized status only.
- Native.Builder / NativelyAI remains showcase/productization.
- AI/ML API and Featherless remain optional provider layers with fallback labels.

## Final Public Hosted Flow

Validated public URLs:

- Frontend showcase: <https://workflow-legion-frontend-production.up.railway.app/>
- Backend health: <https://workflow-legion-production.up.railway.app/health>
- Backend sanitized status: <https://workflow-legion-production.up.railway.app/mission-control-status>

Exact judge demo flow:

1. Open the Band room.
2. Open the public frontend:
   <https://workflow-legion-frontend-production.up.railway.app/>
3. Post in Band:
   `@Workflow Triage Remote Agent AUTO:START WL-INC-003`
4. Show Band agent posts:
   `Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander`
5. Refresh the frontend and show the live hosted Mission Control update.
6. Open backend `/mission-control-status` if needed as raw sanitized proof.

Final architecture boundary:

Workflow Legion uses Band as the live agent collaboration fabric and proof surface. A Railway-hosted backend listens for Band triggers, runs the deterministic five-agent incident workflow, posts visible agent handoffs back into Band, and exports a sanitized Mission Control status feed. A public Railway-hosted frontend displays that live status for judges without exposing secrets or requiring local terminals.

Native.Builder/NativelyAI informed the showcase/productization layer and visual command-center direction. The final live deployment uses Railway for the hosted frontend and backend runtime.

## Current Validated Proof Boundary

- Band room trigger successfully starts the hosted workflow.
- Railway-hosted backend processes the five-agent chain.
- Agents visibly post in Band:
  `Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander`.
- Public Railway frontend reads the hosted sanitized Mission Control status.
- No local terminal listener is required for the public demo.
- Commander is terminal; there is no downstream handoff after Commander.
- `/mission-control-status` is sanitized proof only. It must not expose raw
  Band payloads, room IDs, agent IDs, chat IDs, API keys, `.env` values,
  sponsor codes, QR codes, redemption links, or private credentials.

## Entrypoint

Code:

```text
backend/hosted_runtime.py
```

Start command for a backend-root deployment:

```powershell
python -m uvicorn hosted_runtime:app --host 0.0.0.0 --port $PORT
```

Routes:

```text
GET /health
GET /mission-control-status
```

`/mission-control-status` returns the same Mission Control export shape used by
the frontend showcase. It is allowlisted to status fields only: incident/run
status, role summaries, provider labels, handoff target names, delivery status,
Commander decision status, and timestamps.

## Deployment Variables

Use placeholders in docs and deployment notes. Put real values only in the host
platform's environment variable manager.

```text
APP_ENV=hosted
BAND_BASE_URL=https://app.band.ai/api/v1
BAND_CHAT_ID=<band-chat-id>

BAND_TRIAGE_AGENT_ID=<triage-agent-id>
BAND_TRIAGE_HANDLE=<triage-agent-handle>
BAND_TRIAGE_AGENT_API_KEY=<triage-agent-api-key>

BAND_THREAT_INTEL_AGENT_ID=<threat-intel-agent-id>
BAND_THREAT_INTEL_HANDLE=<threat-intel-agent-handle>
BAND_THREAT_INTEL_AGENT_API_KEY=<threat-intel-agent-api-key>

BAND_FORENSICS_AGENT_ID=<forensics-agent-id>
BAND_FORENSICS_HANDLE=<forensics-agent-handle>
BAND_FORENSICS_AGENT_API_KEY=<forensics-agent-api-key>

BAND_COMPLIANCE_AGENT_ID=<compliance-agent-id>
BAND_COMPLIANCE_HANDLE=<compliance-agent-handle>
BAND_COMPLIANCE_AGENT_API_KEY=<compliance-agent-api-key>

BAND_COMMANDER_AGENT_ID=<commander-agent-id>
BAND_COMMANDER_HANDLE=<commander-agent-handle>
BAND_COMMANDER_AGENT_API_KEY=<commander-agent-api-key>

AUTONOMOUS_AGENT_PROVIDER_MODE=auto
AIML_API_KEY=<optional-aiml-api-key>
AIML_MODEL=<optional-aiml-model>
FEATHERLESS_API_KEY=<optional-featherless-api-key>
FEATHERLESS_MODEL=<optional-featherless-model>

HOSTED_RUNTIME_AUTOSTART=true
HOSTED_RUNTIME_STATE_DIR=.workflow-legion-state
HOSTED_RUNTIME_MISSION_CONTROL_EXPORT=.workflow-legion-state/mission-control-status.hosted.json
HOSTED_RUNTIME_POLL_INTERVAL=5
HOSTED_RUNTIME_MESSAGE_LIMIT=25
HOSTED_RUNTIME_BASELINE_EXISTING=true
HOSTED_RUNTIME_STOP_AFTER_COMPLETE=true
HOSTED_RUNTIME_RESTART_AFTER_COMPLETE=true
```

Provider variables are optional. If they are absent or fail validation, roles
record `provider_mode: deterministic_fallback` and stay inside the bounded demo
evidence.

## Hosted Smoke-Test Checklist

- [ ] Open the public frontend:
  `https://workflow-legion-frontend-production.up.railway.app/`.
- [ ] Open the public backend health URL:
  `https://workflow-legion-production.up.railway.app/health`.
- [ ] Open the public Mission Control/status URL:
  `https://workflow-legion-production.up.railway.app/mission-control-status`.
- [ ] Confirm `/health` returns `service: workflow-legion-hosted-runtime`.
- [ ] Post this in the Band incident room:
  `@Workflow Triage Remote Agent AUTO:START WL-INC-003`.
- [ ] Confirm the hosted runtime processes the chain without a local terminal.
- [ ] Confirm Triage visibly mentions Threat Intel and Forensics in Band.
- [ ] Confirm Threat Intel, Forensics, Compliance, and Commander post through
  their role identities, or the status route honestly shows failed delivery.
- [ ] Confirm all five roles complete, with optional providers either live or
  labeled `deterministic_fallback`.
- [ ] Confirm Commander is terminal: final decision posts and no downstream
  workflow handoff is exported.
- [ ] Refresh the public frontend and confirm Mission Control updates from the
  hosted status feed.
- [ ] Refresh `/mission-control-status` and confirm it shows sanitized Mission
  Control JSON only.

For repeat judge runs, wait until `/health` returns the runtime in `listening`
state again, then post the next supported `AUTO:START WL-INC-00X` message.
