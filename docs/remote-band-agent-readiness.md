# Remote Band Agent Readiness Audit

## Current Validated Proof

The validated live remote proof is the Workflow Triage Remote Agent posting into the Band room through the Band Agent API.

The deterministic five-agent backend workflow is validated by tests and supports reliable replay for judging.

The full five-agent remote Band room is the expansion path and should not be claimed as live until a final smoke test proves all role handoffs resolve to actual Band participants.

## Agent Chain

Required handoff order:

1. Alert Triage Agent mentions Threat Intel Agent and Forensics Agent.
2. Threat Intel Agent mentions Compliance Agent.
3. Forensics Agent mentions Compliance Agent.
4. Compliance Agent mentions Incident Commander Agent.
5. Incident Commander Agent posts the final containment decision.

## Required Remote Handles

Before spawning the full room, confirm the actual Band handles for:

- Triage Agent:
- Threat Intel Agent:
- Forensics Agent:
- Compliance Agent:
- Incident Commander Agent:
- Human observer / Redhood:

These handles must match the Band room participant handles exactly.

## Current Risk

The backend currently supports fallback mention delivery through BAND_DEFAULT_MENTION_HANDLES.

This was useful for the initial remote Triage Agent smoke proof, but it can hide a failed role handoff during full remote-agent testing.

For the final five-agent smoke test, role mentions must resolve directly to their intended agent handles.

A message that falls back to the human observer should be treated as a partial proof, not a full handoff proof.

## Current Backend Behavior

The deterministic workflow can produce five Band-ready messages.

Current endpoint:

POST /api/incidents/wl-inc-001/start

When post_to_band is true, the backend posts workflow messages through the configured Triage Agent API key.

This is valid for demo replay but does not yet prove that five separate remote Band agents posted independently.

## Spawn Gate

Do not spawn or claim the full five-agent remote Band room until:

- [ ] all five Band remote agents exist
- [ ] all five agent handles are known
- [ ] all five agents are participants in the same Band room
- [ ] Triage can mention Threat Intel and Forensics without fallback
- [ ] Threat Intel can mention Compliance without fallback
- [ ] Forensics can mention Compliance without fallback
- [ ] Compliance can mention Commander without fallback
- [ ] Commander can post final decision
- [ ] backend tests pass
- [ ] no .env, API keys, sponsor codes, QR codes, node_modules, dist, or build output are committed

## Demo Language

Allowed:

"The validated live remote proof is the Workflow Triage Remote Agent posting into Band."

"The deterministic five-agent workflow is validated in the backend."

"The full five-agent remote Band room is the expansion path."

Do not say:

"All five remote Band agents are live."

"The full remote room has been proven."

"Band is only a notification layer."
