const consoleLines = [
  "room: band://workflow-legion/WL-INC-001",
  "remote triage: posted via Band Agent API",
  "host: FIN-042 | user: j.morgan",
  "decision: high severity containment recommendation",
];

export function CommandRoomBackdrop() {
  return (
    <div className="command-backdrop" aria-hidden="true">
      <div className="command-grid" />
      <div className="command-screen command-screen--left">
        <span />
        <span />
        <span />
      </div>
      <div className="command-screen command-screen--right">
        <span />
        <span />
        <span />
      </div>
      <div className="signal-map">
        <div className="signal-node signal-node--primary" />
        <div className="signal-node signal-node--intel" />
        <div className="signal-node signal-node--forensics" />
        <div className="signal-node signal-node--compliance" />
        <div className="signal-node signal-node--commander" />
        <div className="signal-line signal-line--one" />
        <div className="signal-line signal-line--two" />
        <div className="signal-line signal-line--three" />
      </div>
      <div className="terminal-strip">
        {consoleLines.map((line) => (
          <span key={line}>{line}</span>
        ))}
      </div>
    </div>
  );
}

