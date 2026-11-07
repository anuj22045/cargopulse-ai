import { apiClient } from "../api/client";

export const SUPPORTED_SHIPPING_MODES = [
  "Same Day",
  "First Class",
  "Second Class",
  "Standard Class",
] as const;

export type ShippingMode = (typeof SUPPORTED_SHIPPING_MODES)[number];

export interface ScenarioResult {
  shipping_mode: string;
  eta_days: number;
  delay_probability: number;
  confidence: number;
  cost: number | null;
}

export interface WhatIfDelta {
  eta_days: number;
  risk_percentage_points: number;
  cost: number | null;
}

export interface WhatIfResult {
  current: ScenarioResult;
  alternative: ScenarioResult;
  delta: WhatIfDelta;
}

export async function simulateWhatIf(
  shipmentId: number,
  alternativeShippingMode: string
): Promise<WhatIfResult> {
  return apiClient("/what-if/simulate", {
    method: "POST",
    body: JSON.stringify({
      shipment_id: shipmentId,
      alternative_shipping_mode: alternativeShippingMode,
    }),
  });
}
