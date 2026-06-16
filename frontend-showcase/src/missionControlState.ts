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

export function isMissionControlState(value: unknown): value is MissionControlState {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<MissionControlState>;
  return (
    typeof candidate.schema_version === "number" &&
    typeof candidate.source_state_file === "string" &&
    typeof candidate.incident_id === "string" &&
    typeof candidate.run_id === "string" &&
    typeof candidate.chain_status === "string" &&
    typeof candidate.current_chain === "string" &&
    typeof candidate.current_role === "string" &&
    Array.isArray(candidate.roles) &&
    candidate.roles.length === 5 &&
    candidate.roles.every(isMissionControlRole) &&
    Array.isArray(candidate.provider_stack) &&
    candidate.provider_stack.every(isProviderStackItem) &&
    isCommanderDecision(candidate.final_commander_decision) &&
    typeof candidate.band_proof_note === "string" &&
    typeof candidate.internal_queue_note === "string" &&
    typeof candidate.created_at === "string" &&
    typeof candidate.updated_at === "string"
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
    missionControlRoleStatuses.has(candidate.status) &&
    typeof candidate.provider === "string" &&
    typeof candidate.provider_mode === "string" &&
    typeof candidate.summary === "string" &&
    Array.isArray(candidate.handoff_targets) &&
    candidate.handoff_targets.every(isString) &&
    isMissionControlDelivery(candidate.delivery) &&
    isNullableString(candidate.completed_at)
  );
}

function isMissionControlDelivery(
  value: unknown,
): value is MissionControlRole["delivery"] {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<MissionControlRole["delivery"]>;
  return (
    typeof candidate.status === "string" &&
    typeof candidate.delivered === "boolean" &&
    isNullableNumber(candidate.status_code) &&
    isNullableString(candidate.attempted_at)
  );
}

function isProviderStackItem(
  value: unknown,
): value is MissionControlState["provider_stack"][number] {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate =
    value as Partial<MissionControlState["provider_stack"][number]>;
  return typeof candidate.provider === "string" && isStringArray(candidate.roles);
}

function isCommanderDecision(
  value: unknown,
): value is MissionControlState["final_commander_decision"] {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate =
    value as Partial<MissionControlState["final_commander_decision"]>;
  return (
    typeof candidate.status === "string" &&
    typeof candidate.summary === "string"
  );
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isNullableNumber(value: unknown): value is number | null {
  return value === null || typeof value === "number";
}
