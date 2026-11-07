"""
Dependency Graph API — Day 17 Phase 2
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dependency_graph_service import (
    get_shipment_dependency_graph,
    upsert_dependency_edge,
)


router = APIRouter(
    prefix="/dependency-graph",
    tags=["Dependency Graph"],
)


# ── Response schemas ──────────────────────────────────────────────────────────

class NodeResponse(BaseModel):
    id: str
    type: str
    entity_id: int | str | None
    label: str
    attributes: dict
    delay_probability: float | None
    severity: str
    impact_status: str
    cost_impact: float | None
    data_source: str


class EdgeResponse(BaseModel):
    source: str
    target: str
    relationship_type: str


class ImpactSummaryResponse(BaseModel):
    delay_probability: float | None
    severity: str
    model_available: bool
    impacted_downstream_count: int
    impacted_downstream_labels: list[str]
    unavailable_count: int
    unavailable_labels: list[str]
    cost_impact: float | None
    cost_impact_note: str
    model_error: str | None


class DependencyGraphResponse(BaseModel):
    shipment_id: int
    nodes: list[NodeResponse]
    edges: list[EdgeResponse]
    explicit_db_edges: list[dict]
    impact_summary: ImpactSummaryResponse
    generated_at: str
    data_notes: list[str]


# ── Edge upsert request ───────────────────────────────────────────────────────

class AddEdgeRequest(BaseModel):
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    relationship_type: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/shipment/{shipment_id}",
    response_model=DependencyGraphResponse,
)
def get_dependency_graph(
    shipment_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve the dependency graph and downstream impact for a shipment.

    Nodes include the shipment itself and all verified connected entities
    (route, carrier, order reference). Missing entities are explicitly
    represented as 'unavailable' — never fabricated.

    Delay impact is derived from the existing ML delay predictor.
    Cost impact is always null (no cost model exists).
    """
    graph = get_shipment_dependency_graph(db=db, shipment_id=shipment_id)

    if graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {shipment_id} not found",
        )

    return graph


@router.post(
    "/edges",
    status_code=status.HTTP_201_CREATED,
)
def add_dependency_edge(
    request: AddEdgeRequest,
    db: Session = Depends(get_db),
):
    """
    Explicitly record a dependency edge in the dependency_graph table.

    Use this to register real supply-chain relationships when the data
    becomes available (e.g. Supplier 42 supplies Shipment 180522).
    """
    edge = upsert_dependency_edge(
        db=db,
        source_type=request.source_type,
        source_id=request.source_id,
        target_type=request.target_type,
        target_id=request.target_id,
        relationship_type=request.relationship_type,
    )
    return {
        "id": edge.id,
        "source_type": edge.source_type,
        "source_id": edge.source_id,
        "target_type": edge.target_type,
        "target_id": edge.target_id,
        "relationship_type": edge.relationship_type,
        "created_at": edge.created_at.isoformat(),
    }
