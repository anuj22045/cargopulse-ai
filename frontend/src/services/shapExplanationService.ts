
import { apiClient } from "../api/client";

export interface SHAPFeatureImportance {
    feature: string;
    value: number;
    impact: "increases risk" | "decreases risk" | "little or no impact";
}

export interface ShipmentExplanation {
    shipment_id: number;
    explanation_method: string;
    output_space: string;
    feature_importances: SHAPFeatureImportance[];
}

export async function getShipmentExplanation(
    shipmentId: number
): Promise<ShipmentExplanation> {
    return apiClient(
    `/shipments/${shipmentId}/explanation`
    );
}


// How does it generate this graph?
// 1. Your trained XGBoost model predicts shipment delay risk.
// 2. SHAP calculates each feature's contribution to that prediction.
// 3. Your backend sends the feature names, values, and impact labels to the React frontend.
// 4. React uses those values to draw the colored bars.