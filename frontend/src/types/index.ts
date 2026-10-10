export interface OracleVerdict {
  success: boolean;
  violated_policies: string[];
  violated_policy: string | null;
  severity: string;
  evidence: Array<{
    policy_id: string;
    description: string;
    step_index: number | null;
    detail: string;
  }>;
  partial_score: number;
  details: Record<string, any>;
}

export interface TraceStep {
  id: string;
  attack_id: string;
  step_index: number;
  role: 'user' | 'assistant' | 'tool_call' | 'tool_result' | 'system';
  content: string;
  tool_name: string | null;
  tool_args: Record<string, any> | null;
  tool_result: Record<string, any> | null;
  is_malicious: boolean;
  timestamp: string;
}

export interface AttackSummary {
  id: string;
  campaign_id: string;
  goal: string;
  category: string;
  strategy: string;
  iteration: number;
  status: 'running' | 'success' | 'failure' | 'error';
  partial_score: number;
  best_in_chain: boolean;
  created_at: string;
  injection_point?: string;
  payload?: string;
}

export interface AttackDetail extends AttackSummary {
  injection_point: string;
  payload: string;
  oracle_verdict: OracleVerdict | null;
  trace_steps: TraceStep[];
}

export interface Campaign {
  id: string;
  created_at: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  goals: string[];
  categories: string[];
  budget_per_goal: number;
  defense_ids: string[];
  config_snapshot: Record<string, any>;
}

export interface ReplayResult {
  id: string;
  attack_id: string;
  n_runs: number;
  successes: number;
  success_rate: number;
  wilson_ci_low: number;
  wilson_ci_high: number;
  defenses_used: string[];
  created_at: string;
}

export interface DefenseInfo {
  id: string;
  name: string;
  description: string;
  enabled?: boolean;
}

export interface EvalMatrixRow {
  id: string;
  campaign_id: string;
  defense_combo: string[];
  attack_success_rate: number;
  benign_pass_rate: number;
  regressions: Record<string, any> | null;
  adaptive_asr: number;
  static_asr: number;
  created_at: string;
}

export interface MetricsSummary {
  campaign_id: string;
  total_attacks: number;
  successful_attacks: number;
  failed_attacks: number;
  error_attacks: number;
  overall_asr: number;
  avg_partial_score: number;
  category_breakdown: Record<string, { total: number; successful: number; asr: number }>;
  strategy_breakdown: Record<string, { total: number; successful: number; asr: number }>;
  wilson_ci?: { low: number; high: number };
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  data: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  is_malicious_path: boolean;
  label: string;
}

export interface AttackGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

