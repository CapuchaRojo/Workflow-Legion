import { SectionHeader } from "./SectionHeader";

const agents = [
  {
    name: "Alert Triage Agent",
    role: "Classifies alert urgency, creates the incident frame, and routes work into the Band room.",
    state: "Validated remote proof",
    tone: "success",
  },
  {
    name: "Threat Intel Agent",
    role: "Enriches indicators, maps suspected tooling, and raises context for malicious activity.",
    state: "Expansion path",
    tone: "info",
  },
  {
    name: "Forensics Agent",
    role: "Builds the host timeline, highlights evidence gaps, and preserves investigation notes.",
    state: "Expansion path",
    tone: "info",
  },
  {
    name: "Compliance Agent",
    role: "Checks audit, escalation, regulated workflow, and reporting implications.",
    state: "Expansion path",
    tone: "warning",
  },
  {
    name: "Incident Commander Agent",
    role: "Turns shared agent context into a containment recommendation and final decision.",
    state: "Expansion path",
    tone: "danger",
  },
];

export function AgentTeam() {
  return (
    <section className="section banded-section" id="agents">
      <div className="container">
        <SectionHeader
          eyebrow="Agent team"
          title="Five roles, one visible incident room"
          body="Workflow Legion models a complete command chain while staying honest about the current validated proof: the remote Triage Agent has posted into Band, and the full five-agent remote room is the next expansion."
        />
        <div className="agent-grid">
          {agents.map((agent) => (
            <article className="agent-card" key={agent.name}>
              <div className="agent-card__topline">
                <span className={`status-dot status-dot--${agent.tone}`} />
                <span className={`status-pill status-pill--${agent.tone}`}>
                  {agent.state}
                </span>
              </div>
              <h3>{agent.name}</h3>
              <p>{agent.role}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

