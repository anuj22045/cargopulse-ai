import { apiClient } from "../api/client";

export interface DecisionHistory {
    id: number;
    shipment_id: number;
    recommendation_id: number | null;
    decision: string;
    decision_reason: string | null;
    actual_outcome: string | null;
    created_at: string;
}

export async function getShipmentDecisions(
    shipmentId: number
): Promise<DecisionHistory[]> {
    return apiClient(
    `/decisions/shipment/${shipmentId}`
    );
}   