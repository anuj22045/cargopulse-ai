import { apiClient } from "../api/client";

export interface AIRecommendation {
    id: number;
    shipment_id: number;
    recommended_action: string;
    reason: string | null;
    expected_delay_reduction: number | null;
    expected_cost: string | null;
    confidence_score: number | null;
    created_at: string;
}

export async function getShipmentRecommendations(
    shipmentId: number    
): Promise<AIRecommendation[]> {
    return apiClient(
    `/ai-recommendations/shipment/${shipmentId}`
    );
}