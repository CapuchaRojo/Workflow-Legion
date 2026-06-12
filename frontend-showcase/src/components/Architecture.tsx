import { SectionHeader } from "./SectionHeader";

const layers = [
  "Frontend Showcase Layer",
  "Python/FastAPI Runtime Layer",
  "Band Coordination Layer",
  "Remote Agent Layer",
  "Optional Provider Support Layer",
];

const endpoints = [
  "GET /health",
  "POST /api/band/test-message",
  "POST /api/incidents/wl-inc-001/start",
  "GET /api/incidents/wl-inc-001/report",
];

export function Architecture() {
  return (
    <section className="section" id="architecture">
      <div className="container">
        <SectionHeader
          eyebrow="Architecture"
          title="Band is the center of coordination"
          body="The static showcase presents the product story. The runtime path keeps agent reasoning lightweight, while Band remains the visible collaboration layer for messages, mentions, handoffs, shared context, and task state."
        />
        <div className="architecture-layout">
          <div className="stack-visual" aria-label="Architecture stack">
            {layers.map((layer) => (
              <div
                className={
                  layer === "Band Coordination Layer"
                    ? "stack-layer stack-layer--band"
                    : "stack-layer"
                }
                key={layer}
              >
                <span>{layer}</span>
                {layer === "Band Coordination Layer" && (
                  <strong>Visible room, messages, mentions, handoffs</strong>
                )}
              </div>
            ))}
          </div>
          <div className="endpoint-panel">
            <div className="panel-label">Static endpoint reference</div>
            <p>
              These are shown as project capability references only. This
              frontend showcase makes no calls.
            </p>
            <div className="endpoint-list">
              {endpoints.map((endpoint) => (
                <code key={endpoint}>{endpoint}</code>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

