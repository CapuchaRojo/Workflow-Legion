import { SectionHeader } from "./SectionHeader";

const team = [
  ["Adam / Redhood", "Product Lead"],
  ["Aditya Choudhry", "Technical Lead"],
  ["Rinor / Rino Yet", "AI / Backend Engineering"],
  ["Logeshwaran R", "Frontend Support"],
  ["Parzival XIII", "QA / Docs / Security"],
  ["Nick Nova", "Mission Realism & Command Review"],
];

export function Team() {
  return (
    <section className="section" id="team">
      <div className="container">
        <SectionHeader
          eyebrow="Team"
          title="Built for demo realism and technical proof"
          body="The team spans product, backend, frontend, mission review, quality, documentation, and security."
        />
        <div className="team-grid">
          {team.map(([name, role]) => (
            <article className="team-card" key={name}>
              <h3>{name}</h3>
              <p>{role}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

