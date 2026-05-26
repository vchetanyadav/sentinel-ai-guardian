const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8090";

export type Incident = {
  id: string;
  title: string;
  severity: "low" | "medium" | "high";
  hypothesis: string;
  proposed_action: string;
  status: string;
  postmortem?: string;
  created_at?: string;
  updated_at?: string;
};

export type ApprovalRequest = {
  request_id: string;
  incident_id: string;
  proposed_action: string;
  rationale: string;
  status: string;
  created_at?: string;
};

export type RunEvent = {
  type: "plan_step" | "tool_call" | "tool_result" | "message";
  timestamp: string;
  label?: string;
  name?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  text?: string;
};

export type Run = {
  run_id: string;
  events: RunEvent[];
};

export async function fetchIncidents(): Promise<Incident[]> {
  const r = await fetch(`${API_BASE}/api/incidents`);
  if (!r.ok) throw new Error("Failed to fetch incidents");
  const data = await r.json();
  return data.incidents;
}

export async function fetchPendingApprovals(): Promise<ApprovalRequest[]> {
  const r = await fetch(`${API_BASE}/api/approvals/pending`);
  if (!r.ok) throw new Error("Failed to fetch approvals");
  const data = await r.json();
  return data.pending;
}

export async function decideApproval(requestId: string, decision: "approve" | "reject") {
  const r = await fetch(`${API_BASE}/api/approvals/${requestId}/decide`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision }),
  });
  if (!r.ok) throw new Error("Failed to submit decision");
  return r.json();
}

export async function fetchRuns() {
  const r = await fetch(`${API_BASE}/api/runs`);
  if (!r.ok) throw new Error("Failed to fetch runs");
  const data = await r.json();
  return data.runs as { run_id: string; event_count: number }[];
}

export async function fetchRun(runId: string): Promise<Run> {
  const r = await fetch(`${API_BASE}/api/runs/${runId}`);
  if (!r.ok) throw new Error("Failed to fetch run");
  return r.json();
}