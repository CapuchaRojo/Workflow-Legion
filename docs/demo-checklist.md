# Demo Checklist

## Final Hosted Public Demo

- [ ] `HOSTED_RUNTIME_DEBUG_RECEIVE=false`.
- [ ] Railway backend service is active.
- [ ] Railway frontend service is active.
- [ ] Public frontend opens:
  `https://workflow-legion-frontend-production.up.railway.app/`.
- [ ] Public backend health opens:
  `https://workflow-legion-production.up.railway.app/health`.
- [ ] Public backend sanitized status opens:
  `https://workflow-legion-production.up.railway.app/mission-control-status`.
- [ ] No local 8080 or 8081 listeners are required or running for the public
  recording.
- [ ] No Railway Variables screens appear in the recording.
- [ ] No secrets, sponsor codes, QR links, redemption links, private
  credentials, Band IDs, room IDs, chat IDs, API keys, `.env` values, raw
  runtime proof JSON, `node_modules`, `dist`, or build output are visible.
- [ ] Band trigger tested with WL-INC-003 or WL-INC-005.
- [ ] Recommended public trigger:
  `@Workflow Triage Remote Agent AUTO:START WL-INC-003`.
- [ ] Band shows:
  `Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander`.
- [ ] Commander is terminal; no downstream handoff appears after Commander.
- [ ] Frontend updates from the hosted sanitized status feed after refresh.

Final architecture language:

Workflow Legion uses Band as the live agent collaboration fabric and proof surface. A Railway-hosted backend listens for Band triggers, runs the deterministic five-agent incident workflow, posts visible agent handoffs back into Band, and exports a sanitized Mission Control status feed. A public Railway-hosted frontend displays that live status for judges without exposing secrets or requiring local terminals.

Native.Builder/NativelyAI informed the showcase/productization layer and visual command-center direction. The final live deployment uses Railway for the hosted frontend and backend runtime.

## Local Repo State

- [ ] Working tree is clean before recording.
- [ ] main is synced with origin/main.
- [ ] No unmerged local demo changes are required.
- [ ] No .env files, API keys, Band keys, sponsor codes, QR codes, node_modules, dist, or build output are staged.

## Backend Validation

Run from repo root:

backend\.venv\Scripts\python.exe -m unittest discover -s tests -v

Required result:

- [ ] All backend tests pass.
- [ ] OK.
- [ ] No secrets printed in terminal output.

## Frontend Showcase Validation

Run from repo root:

cd frontend-showcase
npm install
npm run build
cd ..

Required result:

- [ ] npm install completes.
- [ ] npm run build completes.
- [ ] No vulnerabilities reported for frontend-showcase.
- [ ] dist/ is not committed.

## Band Proof Validation

- [ ] Band proof screenshot exists at docs/screenshots/proof-five-remote-agents-band-post.png.
- [ ] README clearly states the validated proof level.
- [ ] Demo says Workflow Legion now has five validated remote Band agent identities posting into the Band command room through role-specific Band Agent API keys.
- [ ] Demo says the validated posts are Triage, Threat Intel, Forensics, Compliance, and Incident Commander.
- [ ] Demo says no fallback mention-resolution errors were observed.
- [ ] Demo does not claim autonomous live reasoning beyond the validated deterministic workflow and remote Band identity proof.

## Judge Mode

- [ ] Start the local PowerShell supervisor loop with `--message-limit 75` for the current Band room.
- [ ] Judges wait for the terminal `READY` banner before posting the next scenario.
- [ ] Judges post a supported Band trigger such as `@Workflow Triage Remote Agent AUTO:START WL-INC-001`.
- [ ] Backend completes one incident, exports sanitized Mission Control state, restarts the live Band listener, and waits for the next fresh Band trigger.
- [ ] Runtime proof JSON and screenshots stay local unless deliberately sanitized and reviewed.

## Demo Story Validation

- [ ] Incident ID is WL-INC-001.
- [ ] Incident is suspicious PowerShell activity.
- [ ] Host is FIN-042.
- [ ] User is j.morgan.
- [ ] Risk is possible finance data exfiltration.
- [ ] Commander decision is high-severity containment recommendation.
- [ ] Script stays within 2 to 3 minutes.
- [ ] Band is described as the coordination layer, not a notifier.
- [ ] Backend is described as deterministic workflow/runtime logic.
- [ ] Final report output is shown or summarized.
- [ ] Native.Builder / NativelyAI is described as showcase/productization layer.
- [ ] AI/ML API and Featherless are described as optional provider support paths.

## Recording Checklist

- [ ] Open README.
- [ ] Open Band proof screenshot.
- [ ] Show backend tests passing.
- [ ] Show frontend showcase build passing.
- [ ] Walk through frontend-showcase.
- [ ] Show deterministic backend workflow.
- [ ] Show five role-specific remote Band agent posts.
- [ ] Show final report output.
- [ ] End with the value proposition: Workflow Legion turns a chaotic security alert into an auditable, agent-coordinated command-room workflow.

## Final Submission Safety

- [ ] No sponsor redemption codes are visible.
- [ ] No QR codes are visible unless public and approved.
- [ ] No API keys are visible.
- [ ] No .env file is visible.
- [ ] No terminal history exposes secrets.
- [ ] Browser tabs do not expose private accounts, inboxes, or tokens.
- [ ] Claims are honest and match validated proof.
