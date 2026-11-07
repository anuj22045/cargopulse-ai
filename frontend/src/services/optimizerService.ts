import { apiClient } from "../api/client";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ObjectiveWeights {
  w_delay: number;
  w_eta: number;
  w_cost: number;
  w_impact: number;
}

export interface ScoredOption {
  shipping_mode: string;
  delay_probability: number;
  eta_days: number;
  cost: number | null;
  impact: number | null;
  delay_score: number | null;
  eta_score: number | null;
  cost_score: number | null;
  impact_score: number | null;
  composite_score: number;
  effective_weights: Record<string, number>;
  available_objectives: string[];
  is_pareto_optimal: boolean;
}

export interface OptimizerRequest {
  shipment_id: number;
  weights?: Partial<ObjectiveWeights>;
}

export interface OptimizerResponse {
  shipment_id: number;
  ranked_options: ScoredOption[];
  available_objectives: string[];
  unavailable_objectives: string[];
  generated_at: string;
}

// ── Dependency Graph types ────────────────────────────────────────────────────

export interface GraphNode {
  id: string;
  type: string;
  entity_id: number | string | null;
  label: string;
  attributes: Record<string, string | number | null>;
  delay_probability: number | null;
  severity: string;
  impact_status: string;
  cost_impact: number | null;
  data_source: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship_type: string;
}

export interface ImpactSummary {
  delay_probability: number | null;
  severity: string;
  model_available: boolean;
  impacted_downstream_count: number;
  impacted_downstream_labels: string[];
  unavailable_count: number;
  unavailable_labels: string[];
  cost_impact: number | null;
  cost_impact_note: string;
  model_error: string | null;
}

export interface DependencyGraph {
  shipment_id: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  explicit_db_edges: Record<string, unknown>[];
  impact_summary: ImpactSummary;
  generated_at: string;
  data_notes: string[];
}

// ── API calls ─────────────────────────────────────────────────────────────────

export async function runOptimizer(
  shipmentId: number,
  weights: Partial<ObjectiveWeights>
): Promise<OptimizerResponse> {
  return apiClient(`/optimizer/shipment/${shipmentId}`, {
    method: "POST",
    body: JSON.stringify({ weights }),
  });
}

export async function getDependencyGraph(
  shipmentId: number
): Promise<DependencyGraph> {
  return apiClient(`/dependency-graph/shipment/${shipmentId}`);
}
