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

const statusLabels: Record<MissionControlRoleStatus, string> = {
  idle: "Idle",
  running: "Running",
  complete: "Complete",
  failed: "Failed",
  waiting: "Waiting",
};

const statusTones: Record<MissionControlRoleStatus, string> = {
  idle: "info",
  running: "warning",
  complete: "success",
  failed: "danger",
  waiting: "info",
};

export function MissionControl() {
  const { state, source } = useMissionControlFeed();
  const providerLabels = useMemo(
    () => state.provider_stack.map((item) => item.provider).join(" + "),
    [state.provider_stack],
  );

  return (
    <section className="section mission-control-section" id="mission-control">
      <div className="container">
        <SectionHeader
          eyebrow="Mission Control"
          title="Live autonomous runtime visibility"
          body="The backend remains the deterministic autonomous runtime/state machine. This Frontend Studio view is a safe visualization layer over a sanitized local export."
        />

        <div className="mission-shell">
          <div className="mission-summary">
            <div>
              <span className="panel-label">Incident</span>
              <h3>{state.incident_id}</h3>
            </div>
            <div>
              <span className="panel-label">Run</span>
              <h3>{state.run_id}</h3>
            </div>
            <div>
              <span className="panel-label">Chain status</span>
              <h3>{state.chain_status}</h3>
            </div>
            <div>
              <span className="panel-label">Feed</span>
              <h3>{source === "live" ? "Live export" : "Demo fallback"}</h3>
            </div>
          </div>

          <div className="mission-details">
            <article className="mission-panel mission-panel--wide">
              <span className="panel-label">Current chain</span>
              <p className="mission-chain">{state.current_chain}</p>
              <p className="mission-current">Now showing: {state.current_role}</p>
            </article>
            <article className="mission-panel">
              <span className="panel-label">Provider stack</span>
              <p className="provider-labels">{providerLabels}</p>
            </article>
          </div>

          <div className="mission-agent-grid">
            {state.roles.map((role) => (
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
                  <span>{role.provider}</span>
                  <span>{role.provider_mode}</span>
                </div>
                <div className="mission-handoff">
                  <span className="panel-label">Handoff</span>
                  <p>
                    {role.handoff_targets.length
                      ? role.handoff_targets.join(" + ")
                      : "Stop"}
                  </p>
                </div>
                <div className="mission-delivery">
                  Delivery: {role.delivery.status}
                </div>
              </article>
            ))}
          </div>

          <div className="mission-details">
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
              <span className="panel-label">Band proof</span>
              <p>{state.band_proof_note}</p>
              <p>{state.internal_queue_note}</p>
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
