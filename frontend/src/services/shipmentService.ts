import { apiClient } from "../api/client";

export interface Shipment {
    id: number;
  shipment_reference: string;
  order_id: string | null;
  shipping_mode: string | null;
  shipment_status: string | null;
  customer_segment: string | null;
  market: string | null;
  order_region: string | null;
  sales: string | null;
  profit_per_order: string | null;
  quantity: number | null;
  scheduled_shipping_days: number | null;
  current_latitude: number | null;
  current_longitude: number | null;
  created_at: string;
  updated_at: string;
}


export async function getShipments(
  skip: number = 0,
  limit: number = 10,
  shippingMode?: string,
  shipmentStatus?: string,
  search?: string
): Promise<Shipment[]> {

  const params = new URLSearchParams();

  params.append("skip", skip.toString());
  params.append("limit", limit.toString());

  if (shippingMode) {
    params.append("shipping_mode", shippingMode);
  }

  if (shipmentStatus) {
    params.append("shipment_status", shipmentStatus);
  }

  if (search) {
    params.append("search", search);
  }

  return apiClient(
    `/shipments/?${params.toString()}`
  );
}


export async function getShipment(
  shipmentId: number
): Promise<Shipment> {

  return apiClient(
    `/shipments/${shipmentId}`
  );
}