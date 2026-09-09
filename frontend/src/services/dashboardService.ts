import { apiClient } from "../api/client";

export interface DashboardStats {
  total_shipments: number;
  in_transit: number;
  delayed: number;
  delivered: number;
  status_breakdown: { status: string; count: number }[];
  avg_delay_risk: number;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiClient("/dashboard/stats");
}
