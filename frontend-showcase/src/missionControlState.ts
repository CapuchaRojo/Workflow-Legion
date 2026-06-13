export type MissionControlRoleStatus =
  | "idle"
  | "running"
  | "complete"
  | "failed"
  | "waiting";

const missionControlRoleStatuses = new Set<string>([
  "idle",
  "running",
  "complete",
  "failed",
  "waiting",
]);

export type MissionControlRole = {
  role: string;
  display_name: string;
  status: MissionControlRoleStatus;
  provider: string;
  provider_mode: string;
  summary: string;
  handoff_targets: string[];
  delivery: {
    status: string;
    delivered: boolean;
    status_code: number | null;
    attempted_at: string | null;
  };
  completed_at: string | null;
};

export type MissionControlState = {
  schema_version: number;
  source_state_file: string;
  incident_id: string;
  run_id: string;
  chain_status: string;
  current_chain: string;
  current_role: string;
  roles: MissionControlRole[];
  provider_stack: Array<{
    provider: string;
    roles: string[];
  }>;
  final_commander_decision: {
    status: string;
    summary: string;
  };
  band_proof_note: string;
  internal_queue_note: string;
  created_at: string;
  updated_at: string;
};

export const demoMissionControlState: MissionControlState = {
  schema_version: 1,
  source_state_file: ".workflow-legion-state/mission-control-status.json",
  incident_id: "WL-INC-001",
  run_id: "demo-fallback",
  chain_status: "complete",
  current_chain:
    "Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander -> stop",
  current_role: "Incident Commander Agent",
  roles: [
    {
      role: "triage",
      display_name: "Alert Triage Agent",
      status: "complete",
      provider: "aimlapi",
      provider_mode: "deterministic_fallback",
      summary:
        "Classified WL-INC-001 as high severity and opened parallel Threat Intel and Forensics work.",
      handoff_targets: ["Threat Intel Agent", "Forensics Agent"],
      delivery: {
        status: "delivered",
        delivered: true,
        status_code: 201,
        attempted_at: "2026-06-13T00:00:00Z",
      },
      completed_at: "2026-06-13T00:00:01Z",
    },
    {
      role: "threat_intel",
      display_name: "Threat Intel Agent",
      status: "complete",
      provider: "aimlapi",
      provider_mode: "deterministic_fallback",
      summary:
        "Enriched suspicious PowerShell and exfiltration indicators for compliance review.",
      handoff_targets: ["Compliance Agent"],
      delivery: {
        status: "delivered",
        delivered: true,
        status_code: 201,
        attempted_at: "2026-06-13T00:00:02Z",
      },
      completed_at: "2026-06-13T00:00:03Z",
    },
    {
      role: "forensics",
      display_name: "Forensics Agent",
      status: "complete",
      provider: "aimlapi",
      provider_mode: "deterministic_fallback",
      summary:
        "Built the FIN-042 host timeline and preserved evidence gaps for audit context.",
      handoff_targets: ["Compliance Agent"],
      delivery: {
        status: "delivered",
        delivered: true,
        status_code: 201,
        attempted_at: "2026-06-13T00:00:04Z",
      },
      completed_at: "2026-06-13T00:00:05Z",
    },
    {
      role: "compliance",
      display_name: "Compliance Agent",
      status: "complete",
      provider: "featherless",
      provider_mode: "deterministic_fallback",
      summary:
        "Confirmed audit preservation needs and escalated decision authority to Commander.",
      handoff_targets: ["Incident Commander Agent"],
      delivery: {
        status: "delivered",
        delivered: true,
        status_code: 201,
        attempted_at: "2026-06-13T00:00:06Z",
      },
      completed_at: "2026-06-13T00:00:07Z",
    },
    {
      role: "commander",
      display_name: "Incident Commander Agent",
      status: "complete",
      provider: "featherless",
      provider_mode: "deterministic_fallback",
      summary:
        "Issued high-severity containment recommendation for FIN-042 and finance data exposure risk.",
      handoff_targets: [],
      delivery: {
        status: "delivered",
        delivered: true,
        status_code: 201,
        attempted_at: "2026-06-13T00:00:08Z",
      },
      completed_at: "2026-06-13T00:00:09Z",
    },
  ],
  provider_stack: [
    {
      provider: "aimlapi",
      roles: ["Alert Triage Agent", "Threat Intel Agent", "Forensics Agent"],
    },
    {
      provider: "featherless",
      roles: ["Compliance Agent", "Incident Commander Agent"],
    },
  ],
  final_commander_decision: {
    status: "complete",
    summary:
      "High-severity containment recommendation for suspicious PowerShell activity and possible finance data exfiltration on FIN-042.",
  },
  band_proof_note:
    "Band is the collaboration fabric and proof surface: agents coordinate through visible room messages, mentions, handoffs, shared context, and task state.",
  internal_queue_note:
    "The backend deterministic runtime/state machine continues downstream execution through its internal handoff queue only after successful visible Band posts.",
  created_at: "2026-06-13T00:00:00Z",
  updated_at: "2026-06-13T00:00:09Z",
};

export function isMissionControlState(value: unknown): value is MissionControlState {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<MissionControlState>;
  return (
    typeof candidate.incident_id === "string" &&
    typeof candidate.run_id === "string" &&
    typeof candidate.chain_status === "string" &&
    typeof candidate.current_chain === "string" &&
    Array.isArray(candidate.roles) &&
    candidate.roles.every(isMissionControlRole) &&
    Array.isArray(candidate.provider_stack)
  );
}

function isMissionControlRole(value: unknown): value is MissionControlRole {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<MissionControlRole>;
  return (
    typeof candidate.role === "string" &&
    typeof candidate.display_name === "string" &&
    typeof candidate.status === "string" &&
    missionControlRoleStatuses.has(candidate.status)
  );
}
