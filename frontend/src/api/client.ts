import {
  AttackDetail,
  AttackGraph,
  AttackSummary,
  Campaign,
  DefenseInfo,
  EvalMatrixRow,
  MetricsSummary,
  ReplayResult,
} from '../types';

const API_BASE = '/api';

export type WorkspaceRole = 'analyst' | 'owner' | 'auditor' | 'safety_lead';

export const ROLE_LABELS: Record<WorkspaceRole, { title: string; badge: string; desc: string }> = {
  analyst: {
    title: 'Red Team Analyst',
    badge: 'ANALYST',
    desc: 'Runs attack scenarios, views traces & metrics, emergency stops active runs.',
  },
  owner: {
    title: 'Component Owner',
    badge: 'OWNER',
    desc: 'Fixes issues found on owned components, inspects configs & vulnerability risk scores.',
  },
  auditor: {
    title: 'Auditor',
    badge: 'AUDITOR',
    desc: 'Verifies tamper-evident trace hash chains, inspects governance & read-only evidence.',
  },
  safety_lead: {
    title: 'Safety Lead',
    badge: 'ADMIN',
    desc: 'Overall accountability, assign component owners, global emergency kill switch.',
  },
};

export function getActiveRole(): WorkspaceRole {
  if (typeof window !== 'undefined') {
    const stored = sessionStorage.getItem('agentbreak_role') as WorkspaceRole;
    if (stored && (stored === 'analyst' || stored === 'owner' || stored === 'auditor' || stored === 'safety_lead')) {
      return stored;
    }
  }
  return 'safety_lead';
}

export function setActiveRole(role: WorkspaceRole): void {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('agentbreak_role', role);
    window.dispatchEvent(new CustomEvent('agentbreak_role_changed', { detail: role }));
  }
}

async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers || {});
  if (!headers.has('X-Role')) {
    headers.set('X-Role', getActiveRole());
  }
  return fetch(input, { ...init, headers });
}

export async function fetchHealth(): Promise<{ status: string; app: string }> {
  const res = await apiFetch(`${API_BASE}/health`);
  return res.json();
}

export async function loadDemoCampaign(): Promise<{
  status: string;
  campaign_id: string;
  attacks_loaded: number;
  eval_matrix_rows_loaded: number;
}> {
  const res = await apiFetch(`${API_BASE}/demo/load`, { method: 'POST' });
  return res.json();
}

export async function fetchCampaigns(): Promise<Campaign[]> {
  const res = await apiFetch(`${API_BASE}/campaigns`);
  return res.json();
}

export async function fetchScenarios() {
  const res = await apiFetch(`${API_BASE}/scenarios`);
  return res.json();
}

export async function fetchCampaign(id: string): Promise<Campaign> {
  const res = await apiFetch(`${API_BASE}/campaigns/${id}`);
  return res.json();
}

export async function createCampaign(payload: {
  goals: string[];
  categories?: string[];
  budget_per_goal?: number;
  defense_ids?: string[];
}): Promise<Campaign> {
  const res = await apiFetch(`${API_BASE}/campaigns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Failed to create campaign: ${res.status}`);
  }
  return res.json();
}

export async function fetchAttacks(campaignId?: string): Promise<AttackSummary[]> {
  const url = campaignId ? `${API_BASE}/attacks?campaign_id=${campaignId}` : `${API_BASE}/attacks`;
  const res = await apiFetch(url);
  return res.json();
}

export async function fetchAttack(attackId: string): Promise<AttackDetail> {
  const res = await apiFetch(`${API_BASE}/attacks/${attackId}`);
  return res.json();
}

export async function replayAttack(
  attackId: string,
  nRuns: number = 5,
  defenseIds: string[] = []
): Promise<ReplayResult> {
  const res = await apiFetch(`${API_BASE}/attacks/${attackId}/replay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ attack_id: attackId, n_runs: nRuns, defense_ids: defenseIds }),
  });
  return res.json();
}

export async function fetchTraceGraph(attackId: string): Promise<AttackGraph> {
  const res = await apiFetch(`${API_BASE}/traces/${attackId}`);
  return res.json();
}

export async function fetchDefenses(): Promise<DefenseInfo[]> {
  const res = await apiFetch(`${API_BASE}/defenses`);
  return res.json();
}

export async function evaluateDefenses(defenseIds: string[], testPayload?: string) {
  const res = await apiFetch(`${API_BASE}/defenses/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ defense_ids: defenseIds, test_payload: testPayload }),
  });
  return res.json();
}

export async function fetchEvalMatrix(campaignId?: string): Promise<EvalMatrixRow[]> {
  const url = campaignId ? `${API_BASE}/eval/matrix?campaign_id=${campaignId}` : `${API_BASE}/eval/matrix`;
  const res = await apiFetch(url);
  return res.json();
}

export async function runEvalMatrix(campaignId: string, defenseCombos?: string[][]) {
  const res = await apiFetch(`${API_BASE}/eval/matrix`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ campaign_id: campaignId, defense_combos: defenseCombos, include_benign: true }),
  });
  return res.json();
}

export async function fetchMetricsSummary(campaignId?: string): Promise<MetricsSummary> {
  const url = campaignId ? `${API_BASE}/metrics/summary?campaign_id=${campaignId}` : `${API_BASE}/metrics/summary`;
  const res = await apiFetch(url);
  return res.json();
}

export async function fetchReport(campaignId: string, format: 'json' | 'html' = 'json') {
  const res = await apiFetch(`${API_BASE}/reports/${campaignId}?format=${format}`);
  if (format === 'html') {
    return res.text();
  }
  return res.json();
}

export async function fetchValidationExperiments() {
  const res = await apiFetch(`${API_BASE}/validation/experiments`);
  return res.json();
}

export async function createValidationExperiment(payload: any) {
  const res = await apiFetch(`${API_BASE}/validation/experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function fetchPendingApprovals() {
  const res = await apiFetch(`${API_BASE}/approvals/pending`);
  return res.json();
}

export async function approveAction(approvalId: string) {
  const res = await apiFetch(`${API_BASE}/approvals/${approvalId}/approve`, {
    method: 'POST',
  });
  return res.json();
}

export async function rejectAction(approvalId: string) {
  const res = await apiFetch(`${API_BASE}/approvals/${approvalId}/reject`, {
    method: 'POST',
  });
  return res.json();
}

export async function killCampaign(campaignId: string) {
  const res = await apiFetch(`${API_BASE}/campaigns/${campaignId}/kill`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Emergency stop failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchKillswitchStatus() {
  const res = await apiFetch(`${API_BASE}/killswitch/status`);
  return res.json();
}

export async function triggerGlobalKillswitch(reason?: string) {
  const url = reason
    ? `${API_BASE}/killswitch/trigger?reason=${encodeURIComponent(reason)}`
    : `${API_BASE}/killswitch/trigger`;
  const res = await apiFetch(url, { method: 'POST' });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Global kill switch failed: ${res.status}`);
  }
  return res.json();
}

export async function resetGlobalKillswitch() {
  const res = await apiFetch(`${API_BASE}/killswitch/reset`, { method: 'POST' });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Reset kill switch failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchIntegrity(runId: string) {
  const res = await apiFetch(`${API_BASE}/integrity/${encodeURIComponent(runId)}`);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Integrity check failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchGovernanceOwners(): Promise<Array<{ component: string; owner: string }>> {
  const res = await apiFetch(`${API_BASE}/governance/owners`);
  return res.json();
}

export async function updateGovernanceOwner(component: string, owner: string) {
  const res = await apiFetch(`${API_BASE}/governance/owners/${encodeURIComponent(component)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ owner }),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `Governance update failed: ${res.status}`);
  }
  return res.json();
}
