const navItems = [
  { href: "#mission-control", label: "Mission" },
  { href: "#problem", label: "Problem" },
  { href: "#agents", label: "Agents" },
  { href: "#flow", label: "Demo Flow" },
  { href: "#architecture", label: "Architecture" },
  { href: "#sponsors", label: "Sponsors" },
  { href: "#team", label: "Team" },
];

export function Navbar() {
  return (
    <header className="site-header">
      <nav className="container nav-shell" aria-label="Main navigation">
        <a className="brand" href="#hero" aria-label="Workflow Legion home">
          <span className="brand-mark">WL</span>
          <span>
            <strong>Workflow Legion</strong>
            <small>Cyber Incident Command Room</small>
          </span>
        </a>
        <div className="nav-links">
          {navItems.map((item) => (
            <a href={item.href} key={item.href}>
              {item.label}
            </a>
          ))}
        </div>
      </nav>
    </header>
  );
}

