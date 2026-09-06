import { apiClient } from "../api/client";

export interface SimulationEvent {
    id: number;
    shipment_id: number;
    simulation_time: string;
    traffic_status: string | null;
    temperature: number | null;
    humidity: number | null;
    waiting_time: number | null;
    asset_utilization: number | null;
    latitude: number | null;
    longitude: number | null;
}

export async function getShipmentSimulationEvents(
    shipmentId: number
): Promise<SimulationEvent[]> {
    return apiClient(
    `/simulation-events/shipment/${shipmentId}`
    );
}   