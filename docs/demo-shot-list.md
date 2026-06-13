# Demo Shot List

Target video length: 2 to 3 minutes.

## Recording Goals

Show Workflow Legion as an agent-coordinated cyber incident command room.

Keep the story centered on Band.

Do not claim that all five remote agents are live in Band. The validated live remote proof is the Workflow Triage Remote Agent posting into Band through the Band Agent API. The five-agent workflow is currently represented with deterministic backend outputs and is the expansion path for full remote room execution.

## Shot 1: Repository / README

Purpose: Establish project identity and credibility.

Show:
- GitHub repository: CapuchaRojo/Workflow-Legion
- Project name: Workflow Legion
- Cyber Incident Command Room
- Band of Agents Hackathon framing

Narration:
"Workflow Legion is a Band-native cyber incident command room for regulated, high-stakes workflows."

## Shot 2: Band Proof Screenshot

Purpose: Show validated Band integration.

Show:
- docs/screenshots/proof-remote-triage-agent-band-post.png

Narration:
"The validated live remote proof is the Workflow Triage Remote Agent posting successfully into the Band room through the Band Agent API."

Do not say:
- "All five remote agents are live"
- "The full room is production-ready"

Say instead:
"The full five-agent remote Band room is the expansion path."

## Shot 3: Backend Tests Passing

Purpose: Prove deterministic workflow stability.

Show terminal:

python -m unittest discover -s tests -v

Expected:
- Ran 5 tests
- OK

Narration:
"The backend includes deterministic structured outputs for all five incident-response agents, so the demo can be replayed reliably."

## Shot 4: Static Frontend Showcase Build

Purpose: Prove the showcase is reproducible.

Show terminal:

cd frontend-showcase
npm install
npm run build

Expected:
- found 0 vulnerabilities
- built successfully

Narration:
"The static frontend showcase packages the command-room product experience without backend calls, auth, secrets, or environment files."

## Shot 5: Frontend Showcase Walkthrough

Purpose: Present judge-facing product flow.

Show:
- Hero
- Problem and solution
- Agent team
- Demo flow
- Architecture
- Sponsor tools
- Native.Builder / NativelyAI showcase note
- Final CTA

Narration:
"Band coordinates the agents. The backend executes deterministic workflow logic. Native.Builder and NativelyAI package the showcase."

## Shot 6: Incident Scenario

Purpose: Make the cyber scenario concrete.

Show:
- WL-INC-001
- Suspicious PowerShell activity
- Host FIN-042
- User j.morgan
- Possible finance data exfiltration

Narration:
"The demo incident is suspicious PowerShell activity on finance host FIN-042 for user j.morgan, with possible finance data exposure."

## Shot 7: Agent Workflow

Purpose: Show collaboration and handoffs.

Show:
- Alert Triage Agent
- Threat Intel Agent
- Forensics Agent
- Compliance Agent
- Incident Commander Agent

Narration:
"Triage routes the investigation, Threat Intel enriches indicators, Forensics builds the timeline, Compliance checks audit risk, and the Commander issues the containment decision."

## Shot 8: Final Commander Decision

Purpose: End with operational value.

Show final report or deterministic commander output.

Narration:
"The commander classifies this as high severity and recommends containment: isolate FIN-042, reset j.morgan's credentials, preserve PowerShell logs, and continue exfiltration scoping."

## Shot 9: Closing Value Proposition

Purpose: End cleanly.

Show:
- Frontend final CTA or README

Narration:
"Workflow Legion turns a chaotic security alert into an auditable, agent-coordinated command-room workflow."

## Assets Checklist

Use only assets currently available or validated:

- README
- Band proof screenshot
- backend test output
- frontend-showcase local build
- frontend-showcase UI
- deterministic agent outputs
- final incident report output if available
- GitHub PR and issue progress if useful

## Avoid These Claims

Do not claim:
- Workflow Legion prevents breaches
- Workflow Legion replaces SOC teams
- Workflow Legion gives final legal or regulatory advice
- all five remote Band agents are live
- provider APIs are required for the current validated proof
- Native.Builder is the coordination layer

Preferred language:
- accelerates triage
- preserves auditability
- supports command decisions
- Band coordinates agents
- backend executes deterministic workflow logic
- full five-agent remote Band room is the expansion path
