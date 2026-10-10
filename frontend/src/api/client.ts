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

export async function fetchHealth(): Promise<{ status: string; app: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function loadDemoCampaign(): Promise<{
  status: string;
  campaign_id: string;
  attacks_loaded: number;
  eval_matrix_rows_loaded: number;
}> {
  const res = await fetch(`${API_BASE}/demo/load`, { method: 'POST' });
  return res.json();
}

export async function fetchCampaigns(): Promise<Campaign[]> {
  const res = await fetch(`${API_BASE}/campaigns`);
  return res.json();
}

export async function fetchCampaign(id: string): Promise<Campaign> {
  const res = await fetch(`${API_BASE}/campaigns/${id}`);
  return res.json();
}

export async function createCampaign(payload: {
  goals: string[];
  categories?: string[];
  budget_per_goal?: number;
  defense_ids?: string[];
}): Promise<Campaign> {
  const res = await fetch(`${API_BASE}/campaigns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function fetchAttacks(campaignId?: string): Promise<AttackSummary[]> {
  const url = campaignId ? `${API_BASE}/attacks?campaign_id=${campaignId}` : `${API_BASE}/attacks`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchAttack(attackId: string): Promise<AttackDetail> {
  const res = await fetch(`${API_BASE}/attacks/${attackId}`);
  return res.json();
}

export async function replayAttack(
  attackId: string,
  nRuns: number = 5,
  defenseIds: string[] = []
): Promise<ReplayResult> {
  const res = await fetch(`${API_BASE}/attacks/${attackId}/replay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ attack_id: attackId, n_runs: nRuns, defense_ids: defenseIds }),
  });
  return res.json();
}

export async function fetchTraceGraph(attackId: string): Promise<AttackGraph> {
  const res = await fetch(`${API_BASE}/traces/${attackId}`);
  return res.json();
}

export async function fetchDefenses(): Promise<DefenseInfo[]> {
  const res = await fetch(`${API_BASE}/defenses`);
  return res.json();
}

export async function evaluateDefenses(defenseIds: string[], testPayload?: string) {
  const res = await fetch(`${API_BASE}/defenses/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ defense_ids: defenseIds, test_payload: testPayload }),
  });
  return res.json();
}

export async function fetchEvalMatrix(campaignId?: string): Promise<EvalMatrixRow[]> {
  const url = campaignId ? `${API_BASE}/eval/matrix?campaign_id=${campaignId}` : `${API_BASE}/eval/matrix`;
  const res = await fetch(url);
  return res.json();
}

export async function runEvalMatrix(campaignId: string, defenseCombos?: string[][]) {
  const res = await fetch(`${API_BASE}/eval/matrix`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ campaign_id: campaignId, defense_combos: defenseCombos, include_benign: true }),
  });
  return res.json();
}

export async function fetchMetricsSummary(campaignId?: string): Promise<MetricsSummary> {
  const url = campaignId ? `${API_BASE}/metrics/summary?campaign_id=${campaignId}` : `${API_BASE}/metrics/summary`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchReport(campaignId: string, format: 'json' | 'html' = 'json') {
  const res = await fetch(`${API_BASE}/reports/${campaignId}?format=${format}`);
  if (format === 'html') {
    return res.text();
  }
  return res.json();
}

