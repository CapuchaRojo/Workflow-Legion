import { CommandRoomBackdrop } from "./CommandRoomBackdrop";

export function Hero() {
  return (
    <section className="hero" id="hero">
      <CommandRoomBackdrop />
      <div className="container hero-content">
        <div className="hero-copy">
          <span className="eyebrow">Regulated & High-Stakes Workflows</span>
          <h1>Workflow Legion</h1>
          <p className="hero-subtitle">Cyber Incident Command Room</p>
          <p className="hero-claim">
            Band coordinates the agents. Native.Builder packages the showcase.
            Provider APIs support reasoning only when needed.
          </p>
          <div className="hero-badges" aria-label="Project proof points">
            <span>Band-native coordination</span>
            <span>Remote Triage Agent validated</span>
            <span>Static showcase</span>
          </div>
          <div className="hero-actions">
            <a
              className="button button--primary"
              href="https://github.com/CapuchaRojo/Workflow-Legion"
              rel="noreferrer"
              target="_blank"
            >
              GitHub Repository
            </a>
            <a className="button button--ghost" href="#architecture">
              View Architecture
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

