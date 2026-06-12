# Agents

Each agent must communicate through Band.

Implemented deterministic demo agents:

- triage_agent.py
- threat_intel_agent.py
- forensics_agent.py
- compliance_agent.py
- commander_agent.py

Rule: LangGraph can support internal reasoning inside each agent, but Band handles cross-agent coordination.

## Deterministic mock outputs

Issue #28 provides stable structured output for `WL-INC-001` without requiring
an LLM call. Request one agent at a time so Band remains the workflow and
handoff layer:

```python
from agents import get_mock_agent_output

triage = get_mock_agent_output("triage")
print(triage.band_message)
print(triage.mentions)
```

Supported IDs:

- `triage`
- `threat_intel`
- `forensics`
- `compliance`
- `commander`

Each result includes findings, evidence, recommended actions, explicit handoff
targets, and the message to post to Band.
