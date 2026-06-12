import { SectionHeader } from "./SectionHeader";

const steps = [
  "Alert enters Band room",
  "Triage routes investigation",
  "Threat Intel enriches indicators",
  "Forensics builds timeline",
  "Compliance assesses audit/escalation",
  "Commander issues containment decision",
];

export function DemoFlow() {
  return (
    <section className="section" id="flow">
      <div className="container">
        <SectionHeader
          eyebrow="Demo flow"
          title="WL-INC-001 moves through a command chain"
          body="The incident narrative is intentionally concrete: suspicious PowerShell activity on FIN-042, user j.morgan, and possible finance data exfiltration."
        />
        <div className="flow-layout">
          <article className="incident-brief">
            <div className="panel-label">Incident ID</div>
            <h3>WL-INC-001</h3>
            <ul>
              <li>Suspicious PowerShell activity</li>
              <li>Host: FIN-042</li>
              <li>User: j.morgan</li>
              <li>Possible finance data exfiltration</li>
              <li>Commander decision: high severity containment recommendation</li>
            </ul>
          </article>
          <div className="flow-steps">
            {steps.map((step, index) => (
              <article className="flow-step" key={step}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h3>{step}</h3>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

