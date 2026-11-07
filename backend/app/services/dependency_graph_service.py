"""
Dependency Graph Service — Day 17 Phase 2
==========================================

What this service does
----------------------
Builds a node-link dependency graph for a shipment using only
verified relationships stored in the database.

Verified relationships (real data)
------------------------------------
  Shipment -> Route      (via shipments.route_id)
  Shipment -> Carrier    (via shipments.carrier_id)
  Shipment -> OrderRef   (via shipments.order_id — customer order identifier)

Unverified / missing entities
--------------------------------
  Supplier, Factory, Warehouse, Customer entities do not exist as
  first-class tables in this project. No relationships between shipments
  and those entities are stored anywhere.

  Missing upstream/downstream entities are represented with node type
  "unknown" and impact_status "unavailable" — never fabricated.

Downstream delay impact
------------------------
  A shipment is considered DELAYED when its ML-predicted delay_probability
  exceeds DELAY_THRESHOLD (0.5). Delay impact on downstream nodes
  (routes, carriers) is propagated one hop: any connected entity is flagged
  as IMPACTED if the source shipment is DELAYED.

  Severity thresholds (probability-based):
    HIGH    delay_probability >= 0.7
    MEDIUM  delay_probability >= 0.5
    LOW     delay_probability >= 0.3
    NONE    delay_probability <  0.3

Cost impact
-----------
  No shipping-cost model exists. cost_impact is always null.

dependency_graph table usage
-----------------------------
  The existing generic edge table (source_type, source_id, target_type,
  target_id, relationship_type) is used to store explicit edges.
  This service reads verified edges from the DB and also synthesises
  edges from the ORM relationships when no explicit edges are stored.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.models.dependency_graph import DependencyGraph
from app.ai.decision_engine.historical_rates import get_historical_delay_rate
from app.ai.ml.delay_predictor import predict as predict_delay
from app.ai.decision_engine.recommender import (
    build_recommendation_features,
)


# ── Delay severity thresholds ─────────────────────────────────────────────────

DELAY_THRESHOLD_HIGH   = 0.70
DELAY_THRESHOLD_MEDIUM = 0.50
DELAY_THRESHOLD_LOW    = 0.30


def _delay_severity(delay_probability: float) -> str:
    if delay_probability >= DELAY_THRESHOLD_HIGH:
        return "HIGH"
    if delay_probability >= DELAY_THRESHOLD_MEDIUM:
        return "MEDIUM"
    if delay_probability >= DELAY_THRESHOLD_LOW:
        return "LOW"
    return "NONE"


# ── Delay prediction for a shipment ──────────────────────────────────────────

def _predict_shipment_delay(shipment: Shipment) -> dict:
    """
    Run the delay predictor for the shipment's current shipping mode.

    Returns dict with:
      delay_probability (float)
      severity          (str)
      model_available   (bool)
      error             (str | None)
    """
    try:
        prediction_time = datetime.now(timezone.utc)
        features = build_recommendation_features(
            shipment,
            shipping_mode=shipment.shipping_mode,
            prediction_time=prediction_time,
        )
        result = predict_delay(features)
        prob = result["delay_probability"]
        return {
            "delay_probability": prob,
            "severity": _delay_severity(prob),
            "model_available": True,
            "error": None,
        }
    except Exception as exc:
        return {
            "delay_probability": None,
            "severity": "UNKNOWN",
            "model_available": False,
            "error": str(exc),
        }


# ── Node builder helpers ──────────────────────────────────────────────────────

def _shipment_node(shipment: Shipment, delay_info: dict) -> dict:
    """Build the central shipment node."""
    return {
        "id": f"shipment:{shipment.id}",
        "type": "shipment",
        "entity_id": shipment.id,
        "label": shipment.shipment_reference,
        "attributes": {
            "shipping_mode": shipment.shipping_mode,
            "shipment_status": shipment.shipment_status,
            "market": shipment.market,
            "order_region": shipment.order_region,
            "customer_segment": shipment.customer_segment,
            "scheduled_shipping_days": shipment.scheduled_shipping_days,
            "distance_remaining_km": shipment.distance_remaining_km,
        },
        "delay_probability": delay_info["delay_probability"],
        "severity": delay_info["severity"],
        "impact_status": (
            "DELAYED" if delay_info["delay_probability"] is not None
            and delay_info["delay_probability"] >= DELAY_THRESHOLD_MEDIUM
            else "ON_TRACK"
        ) if delay_info["model_available"] else "UNKNOWN",
        "cost_impact": None,     # no cost model
        "data_source": "database",
    }


def _route_node(shipment: Shipment, parent_severity: str) -> dict:
    """Build a node for the shipment's route (real data)."""
    route = shipment.route
    if route is None:
        return {
            "id": f"route:unknown:{shipment.id}",
            "type": "route",
            "entity_id": None,
            "label": "Unknown Route",
            "attributes": {},
            "delay_probability": None,
            "severity": "UNKNOWN",
            "impact_status": "unavailable",
            "cost_impact": None,
            "data_source": "missing",
        }
    return {
        "id": f"route:{route.id}",
        "type": "route",
        "entity_id": route.id,
        "label": route.route_code or f"{route.origin} → {route.destination}",
        "attributes": {
            "origin": route.origin,
            "destination": route.destination,
            "route_code": route.route_code,
        },
        "delay_probability": None,   # routes have no independent prediction
        "severity": parent_severity,  # propagated from shipment
        "impact_status": (
            "IMPACTED" if parent_severity in ("HIGH", "MEDIUM") else "ON_TRACK"
        ),
        "cost_impact": None,
        "data_source": "database",
    }


def _carrier_node(shipment: Shipment, parent_severity: str) -> dict:
    """Build a node for the shipment's carrier (real data when present)."""
    carrier = shipment.carrier
    if carrier is None:
        return {
            "id": f"carrier:unknown:{shipment.id}",
            "type": "carrier",
            "entity_id": None,
            "label": "Unknown Carrier",
            "attributes": {},
            "delay_probability": None,
            "severity": "UNKNOWN",
            "impact_status": "unavailable",
            "cost_impact": None,
            "data_source": "missing",
        }
    return {
        "id": f"carrier:{carrier.id}",
        "type": "carrier",
        "entity_id": carrier.id,
        "label": carrier.name,
        "attributes": {
            "code": carrier.code,
        },
        "delay_probability": None,
        "severity": parent_severity,
        "impact_status": (
            "IMPACTED" if parent_severity in ("HIGH", "MEDIUM") else "ON_TRACK"
        ),
        "cost_impact": None,
        "data_source": "database",
    }


def _order_node(shipment: Shipment, parent_severity: str) -> dict:
    """
    Build an order/customer-order node from shipment.order_id.
    This is a reference ID, not a first-class entity table.
    """
    if not shipment.order_id:
        return {
            "id": f"order:unknown:{shipment.id}",
            "type": "order",
            "entity_id": None,
            "label": "Unknown Order",
            "attributes": {},
            "delay_probability": None,
            "severity": "UNKNOWN",
            "impact_status": "unavailable",
            "cost_impact": None,
            "data_source": "missing",
        }
    return {
        "id": f"order:{shipment.order_id}",
        "type": "order",
        "entity_id": shipment.order_id,
        "label": f"Order {shipment.order_id}",
        "attributes": {
            "customer_segment": shipment.customer_segment,
            "market": shipment.market,
        },
        "delay_probability": None,
        "severity": parent_severity,
        "impact_status": (
            "IMPACTED" if parent_severity in ("HIGH", "MEDIUM") else "ON_TRACK"
        ),
        "cost_impact": None,
        "data_source": "shipment_field",  # derived from shipment.order_id
    }


# ── Explicit DB edges ─────────────────────────────────────────────────────────

def _load_explicit_edges(
    db: Session,
    shipment_id: int,
) -> list[dict]:
    """
    Load any explicitly stored edges from the dependency_graph table
    that reference this shipment.
    """
    rows = db.execute(
        select(DependencyGraph).where(
            (
                (DependencyGraph.source_type == "shipment")
                & (DependencyGraph.source_id == shipment_id)
            )
            | (
                (DependencyGraph.target_type == "shipment")
                & (DependencyGraph.target_id == shipment_id)
            )
        )
    ).scalars().all()

    return [
        {
            "id": row.id,
            "source_type": row.source_type,
            "source_id": row.source_id,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "relationship_type": row.relationship_type,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


# ── Impact summary ────────────────────────────────────────────────────────────

def _build_impact_summary(
    delay_info: dict,
    nodes: list[dict],
) -> dict:
    """
    Summarise downstream impact across the whole graph.
    """
    impacted_nodes = [
        n["label"] for n in nodes
        if n["impact_status"] == "IMPACTED"
    ]
    unavailable_nodes = [
        n["label"] for n in nodes
        if n["impact_status"] == "unavailable"
    ]

    return {
        "delay_probability": delay_info["delay_probability"],
        "severity": delay_info["severity"],
        "model_available": delay_info["model_available"],
        "impacted_downstream_count": len(impacted_nodes),
        "impacted_downstream_labels": impacted_nodes,
        "unavailable_count": len(unavailable_nodes),
        "unavailable_labels": unavailable_nodes,
        "cost_impact": None,          # no cost model
        "cost_impact_note": (
            "Cost impact is unavailable: no shipping-cost model exists "
            "in this project."
        ),
        "model_error": delay_info.get("error"),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_shipment_dependency_graph(
    db: Session,
    shipment_id: int,
) -> dict | None:
    """
    Build and return the dependency graph for a shipment.

    Returns None if the shipment does not exist.

    Graph structure
    ---------------
    {
      "shipment_id": int,
      "nodes": [ { id, type, label, attributes, severity, impact_status,
                   delay_probability, cost_impact, data_source } ],
      "edges": [ { source, target, relationship_type } ],
      "explicit_db_edges": [ raw rows from dependency_graph table ],
      "impact_summary": { ... },
      "generated_at": ISO timestamp,
      "data_notes": [ human-readable caveats ],
    }
    """
    # Load shipment with joined carrier and route
    shipment = db.execute(
        select(Shipment)
        .where(Shipment.id == shipment_id)
    ).scalar_one_or_none()

    if shipment is None:
        return None

    # Explicitly load relationships (avoids lazy-load issues)
    _ = shipment.route
    _ = shipment.carrier

    # Delay prediction
    delay_info = _predict_shipment_delay(shipment)

    # Build nodes
    ship_node     = _shipment_node(shipment, delay_info)
    route_node    = _route_node(shipment, delay_info["severity"])
    carrier_node  = _carrier_node(shipment, delay_info["severity"])
    order_node    = _order_node(shipment, delay_info["severity"])

    nodes = [ship_node, route_node, carrier_node, order_node]

    # Build synthetic edges from ORM relationships
    edges = []
    if shipment.route_id is not None:
        edges.append({
            "source": ship_node["id"],
            "target": route_node["id"],
            "relationship_type": "uses_route",
        })
    if shipment.carrier_id is not None:
        edges.append({
            "source": ship_node["id"],
            "target": carrier_node["id"],
            "relationship_type": "assigned_carrier",
        })
    if shipment.order_id:
        edges.append({
            "source": ship_node["id"],
            "target": order_node["id"],
            "relationship_type": "fulfills_order",
        })

    # Load any explicit edges from DB
    explicit_db_edges = _load_explicit_edges(db, shipment_id)

    # Impact summary
    impact_summary = _build_impact_summary(delay_info, nodes[1:])  # skip ship node itself

    # Data caveats
    data_notes = [
        "Supplier, Factory, and Warehouse entities are not present in "
        "the database schema. Those nodes are omitted — not fabricated.",
        "Carrier data: 0 rows in carriers table. "
        "Carrier node shows 'unavailable' when carrier_id is NULL.",
        "Cost impact is always null (no shipping-cost model exists).",
    ]
    if not delay_info["model_available"]:
        data_notes.append(
            f"Delay prediction unavailable: {delay_info['error']}"
        )

    return {
        "shipment_id": shipment_id,
        "nodes": nodes,
        "edges": edges,
        "explicit_db_edges": explicit_db_edges,
        "impact_summary": impact_summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_notes": data_notes,
    }


def upsert_dependency_edge(
    db: Session,
    source_type: str,
    source_id: int,
    target_type: str,
    target_id: int,
    relationship_type: str,
) -> DependencyGraph:
    """
    Insert a new explicit dependency edge into the dependency_graph table.
    Does not deduplicate — callers are responsible for checking existence.
    Follows the same commit pattern as other services in this project.
    """
    edge = DependencyGraph(
        source_type=source_type,
        source_id=source_id,
        target_type=target_type,
        target_id=target_id,
        relationship_type=relationship_type,
        created_at=datetime.utcnow(),
    )
    db.add(edge)
    try:
        db.commit()
        db.refresh(edge)
    except Exception:
        db.rollback()
        raise
    return edge
