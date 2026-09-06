import { apiClient } from "../api/client";

export interface AIPrediction {
    id: number;
    shipment_id: number;
    delay_probability: number;
    predicted_eta: string | null;
    confidence_score: number | null;
    prediction_time: string;
    model_version: string;
}

export async function getShipmentPredictions(
    shipmentId: number
): Promise<AIPrediction[]> {
    return apiClient(
    `/ai-predictions/shipment/${shipmentId}`
    );
}   