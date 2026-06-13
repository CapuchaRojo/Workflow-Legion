Workflow Legion: Cyber Incident Command Room

Workflow Legion is a Band-native multi-agent cyber incident response system built for the Band of Agents Hackathon.

It demonstrates how specialized incident-response agents can coordinate in a shared Band room, hand off work through @mentions, preserve visible context, and produce an auditable commander decision for a high-stakes security incident.

Mission

Build a SOC-style cyber incident command room where specialized AI agents collaborate through Band to:

triage security alerts,
enrich threat intelligence,
review forensic evidence,
assess compliance and escalation risk,
and produce an auditable incident commander decision.
Core Principle

Band is the collaboration layer.

Agents must communicate, share context, delegate work, and hand off responsibility through Band rooms and Band messages.

Band is not a final notification channel. It is the shared coordination fabric.

Current Validated Proof

The current validated live remote proof is:

Workflow Triage Remote Agent posted successfully into the Band room through the Band Agent API.

Validated repo state:

The current main branch includes the deterministic backend workflow, static frontend showcase, final demo documentation, QA/sponsor safety docs, final report validation, and remote Band agent readiness audit.

Validated locally:

FastAPI backend booted successfully.
GET /health responded successfully.
POST /api/band/test-message delivered a Band message with HTTP 201.
POST /api/incidents/wl-inc-001/start with post_to_band=true delivered deterministic workflow messages through the configured Band client path.
Band participant lookup and dynamic mention resolution are implemented.
.env and backend/.env remain ignored.
.env.example contains placeholders only.
Backend tests pass with 7 tests.
The frontend showcase builds successfully.

Important proof boundary:

The post_to_band=true path proves that the backend can replay the deterministic five-agent workflow into Band through the configured Band client path. It does not prove that all five remote Band agents are live or posting independently.

The validated live remote proof is the Workflow Triage Remote Agent posting into Band through the Band Agent API.

Current Known Limitation

Threat Intel, Forensics, Compliance, and Commander are currently modeled in the deterministic workflow, but they are next-step Band participants unless they are actually created and added to the Band room as remote agents.

Until those role agents are present as Band participants, incident posting may fall back to:

BAND_DEFAULT_MENTION_HANDLES=redhood

The fallback preserves visible role-handoff text in the Band message while routing the actual Band mention payload to an existing participant.

This is intentional and documented so the demo does not overclaim that all five remote agents are live.

The full five-agent remote Band room is the expansion path.

Incident Scenario

Demo incident:

WL-INC-001

Scenario details:

Suspicious PowerShell activity
Possible data exfiltration
Host: FIN-042
User: j.morgan
Risk area: finance data exposure
Outcome: high-severity containment recommendation
Agent Team
Alert Triage Agent

Receives the WL-INC-001 alert, classifies severity, identifies affected host/user, and starts the response chain.

Outputs:

severity,
incident summary,
initial evidence needs,
handoff targets.
Threat Intel Agent

Enriches suspicious indicators, checks likely attack behavior, and assesses external risk.

Outputs:

IOC context,
likely threat behavior,
risk notes.
Forensics Agent

Reviews host activity, PowerShell behavior, process evidence, file activity, and timeline clues.

Outputs:

host timeline,
evidence summary,
forensic confidence.
Compliance Agent

Reviews audit requirements, evidence completeness, reporting implications, and escalation risk.

Outputs:

compliance notes,
audit checklist,
disclosure or escalation recommendation.
Incident Commander Agent

Synthesizes all findings and issues the final command decision.

Outputs:

contain/escalate/monitor decision,
final report summary,
next actions.
MVP Demo Flow
Start the WL-INC-001 incident simulation.
Triage Agent posts the alert into the Band room.
Triage hands off investigation work through visible role text and Band mentions.
Threat Intel enriches indicators.
Forensics reviews endpoint evidence and builds a timeline.
Compliance checks audit and escalation risk.
Commander produces the final incident decision report.
Final state and report are available through the backend API.
Proposed Stack
Band — core collaboration fabric and command room
FastAPI — backend runtime and API layer
Python — agent workflow/runtime logic
Deterministic workflow outputs — safe MVP replay path before all live remote agents are present
LangGraph — optional internal per-agent orchestration only, not the cross-agent coordination layer
React / Vite — judge-facing dashboard/showcase
Redis + ARQ — optional future async job queue
Supabase Postgres or SQLite — optional persistence layer
Native.Builder / NativelyAI — showcase and productization layer
AI/ML API — optional model-provider support path
Featherless — optional open-model provider support path
Backend Endpoints

Useful endpoints:

GET  /health
GET  /api/incidents/wl-inc-001
POST /api/incidents/wl-inc-001/reset
POST /api/incidents/wl-inc-001/start
GET  /api/incidents/wl-inc-001/report
POST /api/band/test-message

Start the incident workflow with Band posting enabled:

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/incidents/wl-inc-001/start `
  -ContentType "application/json" `
  -Body '{"reset": true, "post_to_band": true}' |
  ConvertTo-Json -Depth 20

Proof note:

This path posts deterministic workflow messages through the configured Band client path. It does not prove that all five remote Band agents posted independently.

Current Backend Progress

Implemented:

Typed incident, finding, evidence, timeline, and final report models.
Deterministic outputs for Triage, Threat Intel, Forensics, Compliance, and Commander.
In-memory incident state for the WL-INC-001 demo.
Final incident report generation.
Band client wrapper using the required Band payload shape:
{
  "message": {
    "content": "@handle message text",
    "mentions": [
      {
        "id": "participant-id",
        "handle": "participant-handle",
        "name": "Participant Name"
      }
    ]
  }
}
Live Band participant lookup.
Dynamic mention resolution by handle.
Handle normalization with or without @.
Smoke endpoint for Band delivery testing.
Incident workflow posting through the same Band client path.
Explicit fallback behavior when role agents are not yet Band participants.
Issue Coverage

This backend path supports or advances:

#3 — Band room and test message path
#6 — Alert/Triage Agent path
#11 — Band mention handoff flow
#12 — incident state and findings storage for MVP
#13 — final incident report output
#28 — deterministic mock outputs for all five agents
#29 — backend health, settings, provider router imports, and demo endpoint validation
#34 — remote Triage Agent / Band API smoke proof
Validation Commands
Backend validation

From the repository root:

.\backend\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
deactivate

Expected result:

Ran 7 tests
OK
Frontend showcase validation

From the repository root:

cd frontend-showcase
npm install
npm run build
cd ..

Expected result:

npm install completes with 0 vulnerabilities.
npm run build completes successfully.
Submission and Validation Docs

Key docs:

docs/demo-script.md
docs/demo-shot-list.md
docs/demo-checklist.md
docs/qa-observer-notes.md
docs/sponsor-redemption-checklist.md
docs/final-report-validation.md
docs/remote-band-agent-readiness.md
docs/natively-export-audit.md
docs/tool-usage-doctrine.md
docs/sponsor-credit-strategy.md
docs/natively-builder-showcase.md
Validated Integration Notes
Band + AI/ML API Validation

Workflow Legion’s target architecture is a Band remote-agent system.

Agents run from this repository and connect to Band through the Band API. Band provides the shared command room, participant identity, @mention routing, visible handoffs, shared context, and collaboration audit trail.

During early Band validation, the team confirmed that a Triage Agent could generate a structured WL-INC-001 response using AI/ML API-backed inference.

That internal-agent test is retained as sponsor validation and model-provider proof, but it is not the final runtime architecture.

Current integration direction:

Band — core remote-agent collaboration fabric
Python/FastAPI — agent runtime, deterministic incident workflow, and API layer
AI/ML API — validated model-provider path for Band-connected reasoning experiments
Featherless — planned optional open-model provider for Compliance or Commander reasoning
Native.Builder / NativelyAI — showcase and productization layer, not the core runtime
Static Showcase Page

A static judge-facing showcase page exists under:

frontend-showcase/

Current showcase sections:

Hero
Problem / Solution
Agent Team
Demo Flow
Architecture
Sponsor Tools
Native.Builder section
Team
Final CTA
Footer

Showcase principles:

Fully static.
No backend calls.
No Supabase.
No forms.
No authentication.
No API keys or credentials.
No sponsor codes or QR links.
Band remains the core collaboration layer.
Native.Builder packages the story and presentation; it does not coordinate the agents.

Local showcase build note:

Path: frontend-showcase/
Stack: Vite + React + TypeScript
Validation: npm install; npm run build; build passed with Vite 8.0.16.
Purpose: static hackathon/productization showcase.
Safety: no backend calls, no Supabase, no auth, no forms, no API keys, no environment files, and no secrets.

Native.Builder / NativelyAI was used as a showcase/productization path. The local frontend-showcase/ remains the validated submission showcase, while the downloaded Natively source export is documented in docs/natively-export-audit.md as a backup/proof artifact.

The showcase currently states the honest proof level:

Workflow Triage Remote Agent is validated. The full five-agent remote Band room is the planned expansion path.

Remote Band Agent Readiness

The validated live remote proof is the Workflow Triage Remote Agent posting into the Band room through the Band Agent API.

The deterministic five-agent backend workflow is validated by tests and supports reliable replay for judging.

The full five-agent remote Band room should not be claimed as live until a final smoke test proves all role handoffs resolve to actual Band participants.

Before spawning the full room, confirm the actual Band handles for:

Triage Agent
Threat Intel Agent
Forensics Agent
Compliance Agent
Incident Commander Agent
Human observer / Redhood

Spawn gate:

all five Band remote agents exist,
all five agent handles are known,
all five agents are participants in the same Band room,
Triage can mention Threat Intel and Forensics without fallback,
Threat Intel can mention Compliance without fallback,
Forensics can mention Compliance without fallback,
Compliance can mention Commander without fallback,
Commander can post final decision,
backend tests pass,
no .env, API keys, sponsor codes, QR codes, node_modules, dist, or build output are committed.
Screenshot Archive

Recommended screenshot archive path:

docs/screenshots/

Current proof screenshot:

docs/screenshots/proof-remote-triage-agent-band-post.png

Suggested screenshot caption:

Workflow Triage Remote Agent posting WL-INC-001 workflow messages into the Band command room through the Band Agent API.

Additional screenshots to capture before final submission:

Band room participant list showing Workflow Triage Remote Agent.
Band message timeline showing WL-INC-001 workflow posts.
FastAPI /health response.
FastAPI post_to_band=true incident response.
GitHub repository README.
GitHub project board.
Static showcase landing page hero.
Static showcase architecture section.
Static showcase sponsor tools section.
Safety Notes

Do not commit:

.env
backend/.env
API keys
sponsor codes
QR redemption links
screenshots containing secrets
local databases
logs
__pycache__
node_modules
dist
build output
private credentials
private redemption links

Use .env locally and keep .env.example as placeholders only.

POST /api/band/test-message returns a configuration error instead of attempting live delivery when Band credentials are missing.

Local Backend Quickstart

From the backend directory:

cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Health check:

Invoke-RestMethod `
  -Method Get `
  -Uri http://127.0.0.1:8000/health |
  ConvertTo-Json -Depth 10

Band smoke test:

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/band/test-message `
  -ContentType "application/json" `
  -Body '{"content":"@redhood Workflow Legion backend smoke test: Triage Agent online."}' |
  ConvertTo-Json -Depth 10
Hackathon Positioning

Workflow Legion targets the Regulated & High-Stakes Workflows track.

The project demonstrates:

clear role specialization,
visible multi-agent handoffs,
Band-native coordination,
audit-ready incident context,
command decision synthesis,
and a practical business use case for SOC and compliance teams.
Final Submission Narrative

Workflow Legion turns fragmented incident response into a coordinated command room.

Instead of hidden handoffs, scattered alerts, and unclear ownership, the system uses Band as the visible collaboration layer where agents can route work, preserve shared context, and produce an auditable final decision.

The current demo proves the critical path:

Backend workflow
→ Band Agent API
→ Workflow Triage Remote Agent
→ shared Band command room
→ visible incident handoff messages
→ deterministic five-agent final report
Honest Claim Boundary

Allowed:

Workflow Triage Remote Agent is validated.
The deterministic five-agent workflow is validated in the backend.
Band coordinates the agent workflow.
The backend executes deterministic workflow/runtime logic.
Native.Builder / NativelyAI supports showcase/productization.
AI/ML API and Featherless are optional provider support paths.
The full five-agent remote Band room is the expansion path.

Do not claim:

all five remote Band agents are live,
the full remote room has been proven,
Band is only a notification layer,
provider APIs are required for the validated proof,
Native.Builder coordinates agents,
Workflow Legion prevents breaches,
Workflow Legion replaces SOC teams,
Workflow Legion gives final legal or regulatory advice.