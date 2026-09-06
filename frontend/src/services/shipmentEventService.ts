import { apiClient } from "../api/client";

export interface ShipmentEvent {
  id: number;
  shipment_id: number;
  event_type: string;
  description: string | null;
  latitude: number | null;
  longitude: number | null;
  event_time: string;
  created_at: string;
}

export async function getShipmentEvents(
  shipmentId: number
): Promise<ShipmentEvent[]> {
  return apiClient(
    `/shipment-events/shipment/${shipmentId}`
  );
}