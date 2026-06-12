import { SectionHeader } from "./SectionHeader";

const sponsorTools = [
  {
    name: "Band",
    role: "Core collaboration fabric, highest priority, validated remote Triage Agent posted via Agent API.",
    accent: "blue",
  },
  {
    name: "Native.Builder / NativelyAI",
    role: "Showcase and productization layer only.",
    accent: "green",
  },
  {
    name: "AI/ML API",
    role: "Provider support path, not coordination fabric.",
    accent: "orange",
  },
  {
    name: "Featherless",
    role: "Optional fallback/support path, not required for current validated proof.",
    accent: "red",
  },
];

export function SponsorTools() {
  return (
    <section className="section banded-section" id="sponsors">
      <div className="container">
        <SectionHeader
          eyebrow="Sponsor tools"
          title="Clear roles for every platform"
          body="The project keeps the coordination story clean: Band carries the room, while other tools support packaging or optional provider paths."
        />
        <div className="sponsor-grid">
          {sponsorTools.map((tool) => (
            <article className={`sponsor-card sponsor-card--${tool.accent}`} key={tool.name}>
              <span className="panel-label">{tool.name}</span>
              <p>{tool.role}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

