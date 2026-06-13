# Autonomous Band Runtime

## What Autonomy Means Here

Workflow Legion autonomy means the backend reacts to Band room events instead of
running a pre-scripted five-step poster.

The proof target is:

```text
@redhood/workflow-triage-remote-a AUTO:START WL-INC-001
```

A human posts that one Band message. After that:

1. Triage detects its Band mention and `AUTO:START`.
2. Triage classifies `WL-INC-001`, posts through the Triage Band identity, and
   mentions Threat Intel and Forensics.
3. Threat Intel detects its mention, enriches IOCs, posts through the Threat
   Intel Band identity, and mentions Compliance.
4. Forensics detects its mention, builds an evidence timeline, posts through the
   Forensics Band identity, and mentions Compliance.
5. Compliance deduplicates the two upstream mentions, waits for both upstream
   roles, reviews governance/escalation risk, posts through the Compliance Band
   identity, and mentions Incident Commander.
6. Incident Commander detects its mention, posts the final containment decision
   through the Commander Band identity, and the runtime stops.

Each autonomous output includes a run marker:

```text
[WL-AUTO:<incident_id>:<role>:<run_id>]
```

The marker prevents stale or cross-run messages from waking the wrong role.

## Why The Old Proof Was Different

The previous proof showed remote Band identity/posting behavior: five
role-specific Band agent identities could post deterministic WL-INC-001 messages
into the Band command room through role-specific Band Agent API keys.

That was valuable integration proof, but it was not live autonomous task-agent
execution. The old backend endpoint still exists and remains deterministic:

```text
POST /api/incidents/wl-inc-001/start
```

The new runtime is separate. It is event-driven:

```text
Band message received -> role trigger matched -> task executed -> role posts to Band -> next mention wakes next role
```

## Runtime Receive And React Path

Code entry points:

```text
backend/app/services/autonomous_band_runtime.py
backend/app/services/autonomous_agent_state.py
backend/app/services/autonomous_role_agents.py
backend/run_autonomous_agents.py
```

The receive side is isolated behind `BandEventSource`:

```text
BandEventSource
LiveBandEventSource
ScriptedBandEventSource
```

`ScriptedBandEventSource` powers tests and dry-run. It simulates Band events
without live Band calls while still forcing the dispatcher to wake roles from
message events.

`LiveBandEventSource` is implemented as a polling adapter against the Band Agent
chat messages path. The repo only had validated REST send/participant lookup
code and no local official receive/WebSocket documentation, so this adapter is
intentionally isolated. If Band publishes or confirms an SDK/WebSocket receive
contract, replace `LiveBandEventSource` without changing role logic.

Each role ignores its own authored messages, processes each message ID only once,
and will not rerun after completion. The runtime has a max-turn guard and stops
after Commander.

## Dry-Run

From the repository root:

```powershell
set PYTHONPATH=%CD%\backend
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --dry-run --incident WL-INC-001
```

Expected chain:

```text
Triage -> Threat Intel + Forensics -> Compliance -> Commander -> stop
```

Dry-run writes local structured state to:

```text
.workflow-legion-state/
```

That directory is ignored by Git. The latest Mission Control-friendly status is:

```text
.workflow-legion-state/mission-control-status.json
```

## Live Mode

From the repository root:

```powershell
set PYTHONPATH=%CD%\backend
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py
```

Useful live safety flags:

```text
--poll-interval 5
--run-id operator-check-001
--stop-after-complete
--once
--debug-receive
--dump-recent-messages
--message-limit 5
```

`--poll-interval` controls seconds between live Band receive polls. The default
is `5`.

`--run-id` sets the explicit run ID used in each marker. If omitted, the runtime
generates one.

`--stop-after-complete` is enabled by default and exits after Commander posts the
final decision. `--no-stop-after-complete` keeps the live listener running after
the current run completes.

`--once` / `--single-pass` processes currently available live Band messages once,
then exits. This is useful for safe diagnostics before a full live loop.

Read-only receive diagnostic:

```powershell
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --once --dump-recent-messages --debug-receive
```

Dump mode fetches one recent message batch, prints safe summaries, and exits
without posting agent replies.

Then post exactly one Band room message:

```text
@redhood/workflow-triage-remote-a AUTO:START WL-INC-001
```

Live mode requires:

```text
BAND_BASE_URL
BAND_CHAT_ID
BAND_TRIAGE_HANDLE
BAND_TRIAGE_AGENT_API_KEY
BAND_THREAT_INTEL_HANDLE
BAND_THREAT_INTEL_AGENT_API_KEY
BAND_FORENSICS_HANDLE
BAND_FORENSICS_AGENT_API_KEY
BAND_COMPLIANCE_HANDLE
BAND_COMPLIANCE_AGENT_API_KEY
BAND_COMMANDER_HANDLE
BAND_COMMANDER_AGENT_API_KEY
```

No real keys, chat IDs, or agent IDs belong in Git.

## Provider Routing Plan

Workflow Legion task agents are provider-aware but do not require live provider
keys for tests or dry-run.

AI/ML API is the primary reasoning provider for:

```text
Triage
Threat Intel
Forensics
```

Featherless is the specialist/secondary provider path for:

```text
Compliance
Incident Commander
```

Supported provider env names:

```text
AIML_API_KEY
AIML_BASE_URL
AIML_MODEL
FEATHERLESS_API_KEY
FEATHERLESS_BASE_URL
FEATHERLESS_MODEL
AUTONOMOUS_AGENT_PROVIDER_MODE
```

If provider credentials or models are missing, each role falls back to
deterministic evidence-grounded output and records:

```text
provider_mode: deterministic_fallback
```

`AUTONOMOUS_AGENT_PROVIDER_MODE=deterministic` forces deterministic role output.
`auto` uses a live provider only when credentials and model names are present.

## NativelyAI / Native.Builder Role

NativelyAI and Native.Builder are the Mission Control/productization layer. They
can display the structured state file and showcase the incident chain later, but
they are not the core runtime and do not coordinate task agents.

The backend owns deterministic state transitions. Band owns visible
collaboration, mentions, handoffs, and room context.

## Proof Screenshot Target

Live autonomous proof should be captured here:

```text
docs/screenshots/proof-autonomous-five-agent-band-handoff.png
```

Honest proof boundary:

> Autonomous runtime is not validated live until a Band screenshot shows the full five-agent handoff chain from one human start prompt.
