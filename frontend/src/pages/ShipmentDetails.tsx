import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getShipment, type Shipment } from "../services/shipmentService";
import { getShipmentPredictions, type AIPrediction } from "../services/aiPredictionService";
import { getShipmentSimulationEvents, type SimulationEvent } from "../services/simulationService";
import { getShipmentRecommendations, type AIRecommendation } from "../services/aiRecommendationService";

import { getShipmentDecisions, type DecisionHistory } from "../services/decisionService";

import { getShipmentEvents, type ShipmentEvent } from "../services/shipmentEventService";


function ShipmentDetails() {
  const { shipmentId } = useParams<{ shipmentId: string }>();
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [events, setEvents] = useState<ShipmentEvent[]>([]);
  const [predictions, setPredictions] = useState<AIPrediction[]>([]);
  const [simulationEvents, setSimulationEvents] = useState<SimulationEvent[]>([]);
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [decisions, setDecisions] = useState<DecisionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadShipment() {
      if (!shipmentId) {
        setError("Shipment ID is missing");
        setLoading(false);
        return;
      }
      const id = Number(shipmentId);

      if (Number.isNaN(id)) {
        setError("Invalid shipment ID");
        setLoading(false);
        return;
      }

      try {
        const id = Number(shipmentId);
        const shipmentData = await getShipment(id);
        const eventData = await getShipmentEvents(id);
        const predictionData = await getShipmentPredictions(id);
        const simulationData = await getShipmentSimulationEvents(id);
        const recommendationData = await getShipmentRecommendations(id);
        const decisionData =await getShipmentDecisions(id);

        setShipment(shipmentData);
        setEvents(eventData);
        setPredictions(predictionData);
        setSimulationEvents(simulationData);
        setRecommendations(recommendationData);
        setDecisions(decisionData);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load shipment"
        );
      } finally {
        setLoading(false);
      }
    }

    loadShipment();
  }, [shipmentId]);

  if (loading) {
    return <p>Loading shipment...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  if (!shipment) {
    return <p>Shipment not found.</p>;
  }

  return (
    <div>
      <Link to="/shipments">
        ← Back to Shipments
      </Link>

      <h1>Shipment Details</h1>

      <h2>{shipment.shipment_reference}</h2>

      <div>
        <p>
          <strong>Shipment ID:</strong> {shipment.id}
        </p>

        <p>
          <strong>Order ID:</strong> {shipment.order_id}
        </p>

        <p>
          <strong>Status:</strong> {shipment.shipment_status}
        </p>

        <p>
          <strong>Shipping Mode:</strong> {shipment.shipping_mode}
        </p>

        <p>
          <strong>Customer Segment:</strong>{" "}
          {shipment.customer_segment}
        </p>

        <p>
          <strong>Market:</strong> {shipment.market}
        </p>

        <p>
          <strong>Region:</strong> {shipment.order_region}
        </p>

        <p>
          <strong>Sales:</strong> {shipment.sales}
        </p>

        <p>
          <strong>Profit per Order:</strong>{" "}
          {shipment.profit_per_order}
        </p>

        <p>
          <strong>Quantity:</strong> {shipment.quantity}
        </p>

        <p>
          <strong>Scheduled Shipping Days:</strong>{" "}
          {shipment.scheduled_shipping_days}
        </p>

        <p>
          <strong>Current Latitude:</strong>{" "}
          {shipment.current_latitude}
        </p>

        <p>
          <strong>Current Longitude:</strong>{" "}
          {shipment.current_longitude}
        </p>
      </div>

      <div>
        <h2>Shipment Events</h2>

        {events.length === 0 ? (
          <p>No shipment events found.</p>
        ) : (
          <div>
            {events.map((event) => (
              <div key={event.id}>
                <h3>{event.event_type}</h3>

                <p>
                  <strong>Description:</strong>{" "}
                  {event.description || "No description"}
                </p>

                <p>
                  <strong>Event Time:</strong>{" "}
                  {event.event_time}
                </p>

                <p>
                  <strong>Latitude:</strong>{" "}
                  {event.latitude ?? "N/A"}
                </p>

                <p>
                  <strong>Longitude:</strong>{" "}
                  {event.longitude ?? "N/A"}
                </p>

                <hr />
              </div>
            ))}
          </div>
        )}
      </div>
      <div>
  <h2>AI Prediction History</h2>

  {predictions.length === 0 ? (
    <p>No AI predictions found.</p>
  ) : (
    <div>
      {predictions.map((prediction) => (
        <div key={prediction.id}>
          <h3>
            Prediction #{prediction.id}
          </h3>

          <p>
            <strong>Delay Probability:</strong>{" "}
            {(prediction.delay_probability * 100).toFixed(2)}%
          </p>

          <p>
            <strong>Predicted ETA:</strong>{" "}
            {prediction.predicted_eta || "N/A"}
          </p>

          <p>
            <strong>Confidence:</strong>{" "}
            {prediction.confidence_score !== null
              ? `${(prediction.confidence_score * 100).toFixed(2)}%`
              : "N/A"}
          </p>

          <p>
            <strong>Model Version:</strong>{" "}
            {prediction.model_version}
          </p>

          <p>
            <strong>Prediction Time:</strong>{" "}
            {prediction.prediction_time}
          </p>

            <hr />
            </div>
          ))}
        </div>
      )}
    </div>
    <div>
  <h2>Simulation History</h2>

  {simulationEvents.length === 0 ? (
    <p>No simulation events found.</p>
  ) : (
    <div>
      {simulationEvents.map((simulation) => (
        <div key={simulation.id}>
          <h3>
            Simulation #{simulation.id}
          </h3>

          <p>
            <strong>Simulation Time:</strong>{" "}
            {simulation.simulation_time}
          </p>

          <p>
            <strong>Traffic:</strong>{" "}
            {simulation.traffic_status || "N/A"}
          </p>

          <p>
            <strong>Temperature:</strong>{" "}
            {simulation.temperature ?? "N/A"}
          </p>

          <p>
            <strong>Humidity:</strong>{" "}
            {simulation.humidity ?? "N/A"}
          </p>

          <p>
            <strong>Waiting Time:</strong>{" "}
            {simulation.waiting_time ?? "N/A"}
          </p>

          <p>
            <strong>Asset Utilization:</strong>{" "}
            {simulation.asset_utilization ?? "N/A"}
          </p>

          <p>
            <strong>Latitude:</strong>{" "}
            {simulation.latitude ?? "N/A"}
          </p>

              <p>
            <strong>Longitude:</strong>{" "}
            {simulation.longitude ?? "N/A"}
              </p>

              <hr />
            </div>
          ))}
        </div>
      )}
      </div>
      <div>
  <h2>AI Recommendations</h2>

  {recommendations.length === 0 ? (
    <p>No AI recommendations found.</p>
  ) : (
    <div>
      {recommendations.map((recommendation) => (
        <div key={recommendation.id}>
          <h3>
            {recommendation.recommended_action}
          </h3>

          <p>
            <strong>Reason:</strong>{" "}
            {recommendation.reason || "No reason provided"}
          </p>

          <p>
            <strong>Expected Delay Reduction:</strong>{" "}
            {recommendation.expected_delay_reduction ?? "N/A"}
          </p>

          <p>
            <strong>Expected Cost:</strong>{" "}
            {recommendation.expected_cost ?? "N/A"}
          </p>

          <p>
            <strong>Confidence:</strong>{" "}
            {recommendation.confidence_score !== null
              ? `${(
                  recommendation.confidence_score * 100
                ).toFixed(2)}%`
              : "N/A"}
          </p>

          <p>
            <strong>Created At:</strong>{" "}
            {recommendation.created_at}
          </p>

          <hr />
          </div>
          ))}
        </div>
      )}
    </div>
    <div>
  <h2>Decision History</h2>

  {decisions.length === 0 ? (
    <p>No decisions found.</p>
  ) : (
    <div>
      {decisions.map((decision) => (
        <div key={decision.id}>
          <h3>
            Decision: {decision.decision}
          </h3>

          <p>
            <strong>Recommendation ID:</strong>{" "}
            {decision.recommendation_id ?? "N/A"}
          </p>

          <p>
            <strong>Reason:</strong>{" "}
            {decision.decision_reason || "No reason provided"}
          </p>

          <p>
            <strong>Actual Outcome:</strong>{" "}
            {decision.actual_outcome || "Not available"}
          </p>

          <p>
            <strong>Created At:</strong>{" "}
            {decision.created_at}
          </p>

          <hr />
          </div>
          ))}
        </div>
      )}
    </div>
    </div>
  );
}

export default ShipmentDetails;