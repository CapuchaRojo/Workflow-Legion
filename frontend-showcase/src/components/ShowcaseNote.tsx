export function ShowcaseNote() {
  return (
    <section className="section note-section" id="showcase">
      <div className="container showcase-note">
        <span className="eyebrow">Native.Builder / NativelyAI Showcase</span>
        <h2>Mission Control layer, not the core runtime</h2>
        <p>
          Band coordinates the task agents and provides visible proof through
          room messages, mentions, handoffs, shared context, and task state. The
          backend executes deterministic incident runtime and state-machine
          logic. NativelyAI / Native.Builder productizes that state as a Mission
          Control showcase layer for the hackathon demo.
        </p>
        <p>
          AI/ML API and Featherless remain provider support layers only. They do
          not replace Band as the collaboration fabric or the backend as the
          deterministic runtime.
        </p>
      </div>
    </section>
  );
}

