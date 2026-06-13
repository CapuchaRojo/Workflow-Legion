# Demo Script

## Workflow Legion: Cyber Incident Command Room

Target length: 2 to 3 minutes.

## Opening

Workflow Legion is a cyber incident command room built for regulated, high-stakes workflows.

The core idea is simple: when a serious security incident starts, the problem is not just detection. The problem is coordination. Teams need triage, enrichment, forensic context, compliance awareness, and a decisive command decision without losing the audit trail.

Workflow Legion uses Band as the agent coordination layer. Band is not treated as a notifier or wrapper. Band is where the agents coordinate, hand off work, and keep the incident visible.

## Demo Scenario

The demo incident is WL-INC-001.

A suspicious PowerShell activity alert appears on finance host FIN-042 for user j.morgan. The risk is possible finance data exfiltration.

Workflow Legion now has five validated remote Band agent identities posting into the Band command room through role-specific Band Agent API keys: Triage, Threat Intel, Forensics, Compliance, and Incident Commander. No fallback mention-resolution errors were observed. The backend workflow is deterministic so the incident can be replayed reliably during judging.

## Walkthrough

First, the incident starts with a suspicious PowerShell alert.

The Alert Triage Agent classifies the alert and routes the investigation. It identifies the affected host, the user, and the suspected risk. This creates the command-room starting point inside Band.

Next, the Threat Intel Agent enriches the indicators. It looks at suspicious command behavior, possible exfiltration patterns, and whether the activity resembles known attacker tradecraft.

Then the Forensics Agent builds the investigation timeline. It focuses on what happened first, what evidence must be preserved, and what system artifacts matter: PowerShell logs, host activity, authentication context, and related finance-system access.

After that, the Compliance Agent reviews audit and escalation concerns. It does not make legal conclusions. It highlights that this is a regulated data-risk scenario where evidence preservation, escalation tracking, and decision records matter.

Finally, the Incident Commander Agent produces the decision. The commander classifies the incident as high severity and recommends containment: isolate FIN-042, reset j.morgan's credentials, preserve PowerShell logs, and continue scoping for possible finance data exposure.

The proof screenshot shows the five role-specific remote Band posts. The final report output shows the deterministic commander decision and audit trail.

## Architecture Message

The architecture is intentionally layered.

Band coordinates agents.

The backend executes deterministic incident workflow logic.

The static frontend showcase presents the command-room product experience.

Native.Builder and NativelyAI are used as the showcase and productization layer.

AI/ML API and Featherless are optional provider support paths. They are not the coordination fabric.

This demo does not claim autonomous live reasoning beyond the validated deterministic workflow plus remote Band identity proof.

## Closing

Workflow Legion turns a chaotic security alert into an auditable, agent-coordinated command-room workflow.

It shows how specialized agents can collaborate around a regulated incident while keeping the human commander focused on decision quality, evidence preservation, and containment.
