import { SectionHeader } from "./SectionHeader";

export function ProblemSolution() {
  return (
    <section className="section" id="problem">
      <div className="container">
        <SectionHeader
          eyebrow="Problem + Solution"
          title="Incident response breaks when agents vanish into a black box"
          body="High-stakes teams need visible coordination, accountable handoffs, and a shared room where humans can inspect the reasoning path."
        />
        <div className="split-grid">
          <article className="summary-card summary-card--danger">
            <span className="panel-label">Problem</span>
            <h3>Disconnected automation cannot carry regulated incident work.</h3>
            <p>
              A backend-only orchestrator may produce a final answer, but it
              hides the collaboration trail that security, compliance, and
              command reviewers need during a live response.
            </p>
          </article>
          <article className="summary-card summary-card--success">
            <span className="panel-label">Solution</span>
            <h3>Band becomes the visible coordination fabric.</h3>
            <p>
              Workflow Legion puts messages, mentions, shared context, and
              task state in the Band room so the response chain is inspectable
              while agents work.
            </p>
          </article>
        </div>
        <div className="proof-strip">
          <div>
            <span className="panel-label">Validated proof</span>
            <strong>
              Workflow Triage Remote Agent posted successfully into the Band
              room through the Band Agent API.
            </strong>
          </div>
          <p>
            The current validated proof is the remote Triage Agent. The full
            five-agent remote room is the expansion path, not a claim of current
            live coverage.
          </p>
        </div>
      </div>
    </section>
  );
}

