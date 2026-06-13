# Demo Checklist

## Local Repo State

- [ ] Working tree is clean before recording.
- [ ] main is synced with origin/main.
- [ ] No unmerged local demo changes are required.
- [ ] No .env files, API keys, Band keys, sponsor codes, QR codes, node_modules, dist, or build output are staged.

## Backend Validation

Run from repo root:

python -m unittest discover -s tests -v

Required result:

- [ ] Ran 5 tests.
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

- [ ] Band proof screenshot exists at docs/screenshots/proof-remote-triage-agent-band-post.png.
- [ ] README clearly states the validated proof level.
- [ ] Demo says the Workflow Triage Remote Agent is validated.
- [ ] Demo does not claim all five remote agents are live.
- [ ] Demo says the full five-agent remote Band room is the expansion path.

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
- [ ] Native.Builder / NativelyAI is described as showcase/productization layer.
- [ ] AI/ML API and Featherless are described as optional provider support paths.

## Recording Checklist

- [ ] Open README.
- [ ] Open Band proof screenshot.
- [ ] Show backend tests passing.
- [ ] Show frontend showcase build passing.
- [ ] Walk through frontend-showcase.
- [ ] Show final report or deterministic commander output if available.
- [ ] End with the value proposition: Workflow Legion turns a chaotic security alert into an auditable, agent-coordinated command-room workflow.

## Final Submission Safety

- [ ] No sponsor redemption codes are visible.
- [ ] No QR codes are visible unless public and approved.
- [ ] No API keys are visible.
- [ ] No .env file is visible.
- [ ] No terminal history exposes secrets.
- [ ] Browser tabs do not expose private accounts, inboxes, or tokens.
- [ ] Claims are honest and match validated proof.
