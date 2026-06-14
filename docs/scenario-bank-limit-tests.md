# Phase 4 Scenario-Bank Limit Tests

## Purpose

Phase 4 adds a small bank of deterministic incident scenarios so the existing
five-agent runtime can be dry-run tested, and later manually live-tested in
Band, beyond the original `WL-INC-001` demo.

This is limit testing for the validated runtime path, not a replacement
orchestrator and not a live intelligence integration. The backend still owns
deterministic workflow and state-machine logic. Band remains the collaboration
fabric and proof surface where agents visibly coordinate through room messages,
mentions, handoffs, shared context, and task state.

AI/ML API and Featherless remain optional provider support layers. Mission
Control reads sanitized JSON export only; it is a visibility and productization
surface, not the agent coordinator.

Runtime proof JSON files under `.workflow-legion-state/` are local-only and
must not be committed.

## Supported Scenarios

| Incident ID | Title | Host | User | Department |
| --- | --- | --- | --- | --- |
| `WL-INC-001` | Suspicious PowerShell Activity and Possible Data Exfiltration | `FIN-042` | `j.morgan` | Finance |
| `WL-INC-002` | Credential Stuffing and Impossible Travel | `IDP-EDGE-01` | `s.patel` | Finance |
| `WL-INC-003` | Vendor Invoice Fraud / Business Email Compromise | `MAIL-SEC-02` | `a.lee` | Accounts Payable |
| `WL-INC-004` | Cloud Storage Exposure / Public Bucket | `CLOUD-STORAGE-01` | `svc-data-export` | Data Operations |
| `WL-INC-005` | Malware Beacon / Suspicious DNS | `ENG-117` | `r.kim` | Engineering |

## Validated Chain

The runtime chain remains:

```text
Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander -> stop
```

Commander is terminal. The Commander role has no downstream workflow handoff
targets.

## Dry-Run Commands

Run these from the repository root. Dry-runs do not call live Band or provider
APIs.

```powershell
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --dry-run --incident WL-INC-002 --state-dir .workflow-legion-state\scenario-bank --run-id dry-wl-inc-002
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --dry-run --incident WL-INC-003 --state-dir .workflow-legion-state\scenario-bank --run-id dry-wl-inc-003
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --dry-run --incident WL-INC-004 --state-dir .workflow-legion-state\scenario-bank --run-id dry-wl-inc-004
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --dry-run --incident WL-INC-005 --state-dir .workflow-legion-state\scenario-bank --run-id dry-wl-inc-005
```

Expected result for each dry-run:

- Five role outputs: `triage`, `threat_intel`, `forensics`, `compliance`,
  `commander`
- Final status: `complete`
- Commander handoff targets: none
- Local state files only under the selected state directory

## Manual Live Band Tests

Live Band testing is manual/operator-triggered. Start the receiver first, then
post the matching Band room message mentioning the Triage remote agent. The
incident ID is read from the Band message.

For `WL-INC-002`:

```powershell
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --poll-interval 3 --max-turns 8 --message-limit 25 --stop-after-complete --debug-receive --ignore-existing --frontend-studio-export frontend-showcase\public\mission-control-status.json --run-id live-wl-inc-002
```

Band room message:

```text
@<triage-remote-handle> AUTO:START WL-INC-002
```

For `WL-INC-003`:

```powershell
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --poll-interval 3 --max-turns 8 --message-limit 25 --stop-after-complete --debug-receive --ignore-existing --frontend-studio-export frontend-showcase\public\mission-control-status.json --run-id live-wl-inc-003
```

Band room message:

```text
@<triage-remote-handle> AUTO:START WL-INC-003
```

For `WL-INC-004`:

```powershell
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --poll-interval 3 --max-turns 8 --message-limit 25 --stop-after-complete --debug-receive --ignore-existing --frontend-studio-export frontend-showcase\public\mission-control-status.json --run-id live-wl-inc-004
```

Band room message:

```text
@<triage-remote-handle> AUTO:START WL-INC-004
```

For `WL-INC-005`:

```powershell
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --poll-interval 3 --max-turns 8 --message-limit 25 --stop-after-complete --debug-receive --ignore-existing --frontend-studio-export frontend-showcase\public\mission-control-status.json --run-id live-wl-inc-005
```

Band room message:

```text
@<triage-remote-handle> AUTO:START WL-INC-005
```

Use `--stop-after-complete` if you want the runner to exit after the Commander
post. It is the default behavior.
