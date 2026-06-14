import { useEffect, useMemo, useState } from "react";
import { SectionHeader } from "./SectionHeader";
import {
  demoMissionControlState,
  isMissionControlState,
  type MissionControlRoleStatus,
  type MissionControlState,
} from "../missionControlState";

const LIVE_STATUS_PATH = "/mission-control-status.json";
const POLL_INTERVAL_MS = 2500;

type StatusTone = "info" | "warning" | "success" | "danger";

const statusLabels: Record<MissionControlRoleStatus, string> = {
  idle: "Idle",
  running: "Running",
  complete: "Complete",
  failed: "Failed",
  waiting: "Waiting",
};

const statusTones: Record<MissionControlRoleStatus, StatusTone> = {
  idle: "info",
  running: "warning",
  complete: "success",
  failed: "danger",
  waiting: "info",
};

const missionLayerCards = [
  {
    label: "Visible coordination",
    title: "Band coordinates agents",
    body: "Room messages, mentions, handoffs, shared context, and task state stay visible for demo proof.",
  },
  {
    label: "Deterministic runtime",
    title: "Backend executes state logic",
    body: "The Python/FastAPI runtime owns the incident state machine and exports sanitized status JSON.",
  },
  {
    label: "Productization layer",
    title: "Natively shapes Mission Control",
    body: "Native.Builder frames the showcase layer without replacing Band or the backend runtime.",
  },
];

export function MissionControl() {
  const { state, source } = useMissionControlFeed();
  const providerLabels = useMemo(
    () =>
      state.provider_stack
        .map((item) => `${item.provider} (${item.roles.length})`)
        .join(" + ") || "Provider labels pending",
    [state.provider_stack],
  );
  const deliverySummary = useMemo(() => {
    const delivered = state.roles.filter((role) => role.delivery?.delivered).length;
    return `${delivered}/${state.roles.length} Band deliveries`;
  }, [state.roles]);
  const feedLabel = source === "live" ? "Live export" : "Demo fallback";

  return (
    <section className="section mission-control-section" id="mission-control">
      <div className="container">
        <SectionHeader
          eyebrow="Mission Control"
          title="Natively-style showcase over live runtime state"
          body="This view productizes the command room without changing the runtime contract: Band is the visible collaboration fabric, the backend executes deterministic state logic, and the frontend polls sanitized Mission Control JSON."
        />

        <div className="mission-shell mission-shell--showcase">
          <div className="mission-feed-strip" aria-label="Mission Control feed status">
            <span className={`status-dot status-dot--${source === "live" ? "success" : "warning"}`} />
            <span>{feedLabel}</span>
            <span>Polling /mission-control-status.json every 2.5s</span>
            <span>No credentials embedded</span>
          </div>

          <div className="mission-summary">
            <div className="mission-summary-card mission-summary-card--primary">
              <span className="panel-label">Incident ID</span>
              <h3>{state.incident_id}</h3>
              <p>Suspicious PowerShell and possible data exfiltration on FIN-042.</p>
            </div>
            <div className="mission-summary-card">
              <span className="panel-label">Run ID</span>
              <h3>{state.run_id}</h3>
              <p>Runtime export source: {state.source_state_file}</p>
            </div>
            <div className="mission-summary-card">
              <span className="panel-label">Chain status</span>
              <h3>{state.chain_status}</h3>
              <p>{deliverySummary}</p>
            </div>
            <div className="mission-summary-card">
              <span className="panel-label">Provider labels</span>
              <h3>{providerLabels}</h3>
              <p>AI/ML API and Featherless remain support layers, not coordination fabric.</p>
            </div>
          </div>

          <div className="mission-command-grid">
            <article className="mission-panel mission-panel--wide mission-current-panel">
              <div className="mission-panel-header">
                <span className="panel-label">Current chain</span>
                <span className={`status-pill status-pill--${toneForStatus(state.chain_status)}`}>
                  {state.chain_status}
                </span>
              </div>
              <p className="mission-chain">{state.current_chain}</p>
              <div className="mission-current-row">
                <span>Now showing</span>
                <strong>{state.current_role}</strong>
              </div>
            </article>
            <article className="mission-panel mission-builder-panel">
              <div className="mission-builder-brand">
                <img
                  alt="NativelyAI"
                  height="32"
                  src="/nativelyai.svg"
                  width="32"
                />
                <div>
                  <span className="panel-label">Natively / Native.Builder</span>
                  <h3>Mission Control productization layer</h3>
                </div>
              </div>
              <p>
                The Natively presentation layer makes the incident command state
                readable for demos, judges, and stakeholders. It does not own
                agent coordination or runtime execution.
              </p>
            </article>
          </div>

          <div className="mission-layer-grid" aria-label="Mission Control architecture roles">
            {missionLayerCards.map((card) => (
              <article className="mission-layer-card" key={card.title}>
                <span>{card.label}</span>
                <h3>{card.title}</h3>
                <p>{card.body}</p>
              </article>
            ))}
          </div>

          <div className="mission-agent-heading">
            <div>
              <span className="panel-label">Five task agents</span>
              <h3>Band-visible role status</h3>
            </div>
            <p>
              Agents are task agents, not general chatbots. Each card shows
              status, provider mode, handoff target, and Band delivery state.
            </p>
          </div>

          <div className="mission-agent-grid mission-agent-grid--runtime">
            {state.roles.map((role) => {
              const delivery = role.delivery ?? {
                attempted_at: null,
                delivered: false,
                status: "pending",
                status_code: null,
              };

              return (
                <article className="mission-agent-card" key={role.role}>
                  <div className="agent-card__topline">
                    <span
                      className={`status-dot status-dot--${statusTones[role.status]}`}
                    />
                    <span
                      className={`status-pill status-pill--${statusTones[role.status]}`}
                    >
                      {statusLabels[role.status]}
                    </span>
                  </div>
                  <h3>{role.display_name}</h3>
                  <p>{role.summary || "Waiting for runtime output."}</p>
                  <div className="mission-card-meta">
                    <span>Provider: {role.provider}</span>
                    <span>Mode: {role.provider_mode}</span>
                  </div>
                  <div className="mission-handoff">
                    <span className="panel-label">Handoff</span>
                    <p>
                      {role.handoff_targets.length
                        ? role.handoff_targets.join(" + ")
                        : "Stop"}
                    </p>
                  </div>
                  <div className="mission-delivery-row">
                    <span>Band delivery</span>
                    <strong className={`status-pill status-pill--${toneForStatus(delivery.status)}`}>
                      {delivery.status}
                    </strong>
                    <small>
                      {delivery.status_code !== null
                        ? `HTTP ${delivery.status_code}`
                        : "status code pending"}
                    </small>
                  </div>
                </article>
              );
            })}
          </div>

          <div className="mission-proof-grid">
            <article className="mission-panel mission-panel--wide">
              <span className="panel-label">Commander decision</span>
              <p>
                {state.final_commander_decision.summary ||
                  "Pending Incident Commander decision."}
              </p>
              <span className="mission-decision-status">
                {state.final_commander_decision.status}
              </span>
            </article>
            <article className="mission-panel mission-panel--wide">
              <span className="panel-label">Proof screenshot / proof note</span>
              <p>{state.band_proof_note}</p>
              <small>
                Screenshot proof remains external Band room evidence. This panel
                displays only the sanitized proof note from the Mission Control
                export.
              </small>
            </article>
            <article className="mission-panel mission-panel--wide">
              <span className="panel-label">Internal handoff queue</span>
              <p>{state.internal_queue_note}</p>
              <small>
                The queue is deterministic execution bookkeeping. Band remains
                the shared command room and proof surface.
              </small>
            </article>
          </div>
        </div>
      </div>
    </section>
  );
}

function useMissionControlFeed(): {
  state: MissionControlState;
  source: "live" | "demo";
} {
  const [state, setState] = useState<MissionControlState>(
    demoMissionControlState,
  );
  const [source, setSource] = useState<"live" | "demo">("demo");

  useEffect(() => {
    let cancelled = false;

    async function loadStatus() {
      try {
        const response = await fetch(LIVE_STATUS_PATH, {
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error("Mission Control export is not available.");
        }

        const payload: unknown = await response.json();
        if (!isMissionControlState(payload)) {
          throw new Error("Mission Control export shape is invalid.");
        }

        if (!cancelled) {
          setState(payload);
          setSource("live");
        }
      } catch {
        if (!cancelled) {
          setState(demoMissionControlState);
          setSource("demo");
        }
      }
    }

    void loadStatus();
    const interval = window.setInterval(loadStatus, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return { state, source };
}

function toneForStatus(status: string): StatusTone {
  const normalized = status.toLowerCase();
  if (normalized.includes("fail") || normalized.includes("error")) {
    return "danger";
  }
  if (normalized.includes("complete") || normalized.includes("deliver")) {
    return "success";
  }
  if (normalized.includes("run") || normalized.includes("wait")) {
    return "warning";
  }
  return "info";
}
