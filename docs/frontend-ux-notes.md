Frontend UX Notes



These notes review the local Workflow Legion frontend showcase and identify final polish opportunities for the demo/submission flow.



Current Proof Context



Workflow Legion now has five validated remote Band agent identities posting into the Band command room through role-specific Band Agent API keys:



Triage

Threat Intel

Forensics

Compliance

Incident Commander



Band is the core collaboration fabric. The backend remains the deterministic workflow/runtime layer. Native.Builder/NativelyAI is the showcase/productization layer. AI/ML API and Featherless remain optional provider support layers.



Desktop View

Strengths

The color gradients fit the cyber-operations theme.

Spacing between major sections is generally clear.

Buttons are responsive and easy to identify.

The page is simple to walk through during a demo.

The content gives judges a comprehensive overview of the system.

The section structure is modular and easy to scan.

Confusing Elements

The hero chips, such as “Band-native coordination,” “remote agent validation,” and “static showcase,” may look clickable even when they are informational.

The proof section should not be removed, but it should be named clearly as current five-agent proof.

In the demo flow section, the “Example Incident” and “Flow” areas could use stronger visual hierarchy.

In the architecture section, static endpoint references may distract non-technical viewers if they are too prominent.

Repeated Native.Builder/NativelyAI references should be checked so the showcase layer is clear without making it look like the core orchestration layer.

Recommended Improvements

Rename the proof section to “Validated Five-Agent Band Proof.”

Make major section headers larger and easier to scan.

Add stronger visual styling to the problem and solution sections.

Center the “Live Demo: Coming Soon” button with the GitHub repo and demo video buttons, or make its disabled/placeholder state more obvious.

Add a “Back to Top” control if time permits.

Increase edge margin consistency so content does not feel tight on wide screens.

Suggested Label Updates

Rename “Agent Team” to “Agent Workforce” if the team wants a more operational tone.

Under Agent Workforce, use outcome-based labels:

Triage: Incident Validation

Threat Intel: Threat Attribution

Forensics: Evidence Timeline

Compliance: Governance Review

Incident Commander: Containment Decision

Under Architecture, consider a heading such as “System Architecture Layers” or “Band-Centric Coordination Architecture.”

Mobile and Tablet View

Strengths

Mobile and tablet alignment looks strong overall.

The page remains responsive and easy to walk through.

Buttons remain usable on smaller screens.

The content flow is easier to scan than the desktop layout in some areas.

Mobile Polish Item



The header chips, such as “room,” “remote agent,” and “decision panel,” should be checked for overflow near the GitHub repo and architecture buttons.



Demo Guidance



For the final demo, preserve this framing:



Start with the problem and the incident scenario.

Show the deterministic backend workflow producing role outputs.

Show Band as the coordination fabric where the five remote agent identities post.

Show the final report and recommended containment actions.

Show the static frontend showcase as the productization/demo layer.



Do not describe Band as a notifier. Band coordinates the agent collaboration layer while the backend executes deterministic workflow/runtime logic.

