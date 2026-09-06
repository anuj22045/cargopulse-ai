from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Shipment

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated stats for the dashboard:
    - total shipments
    - in_transit count  (status = 'Shipping')
    - delayed count     (status = 'Late delivery')
    - delivered count   (status = 'Delivered')
    - status breakdown  [{status, count}]
    """
    # Aggregate counts by status in a single query
    rows = db.execute(
        select(
            Shipment.shipment_status,
            func.count(Shipment.id).label("count")
        )
        .group_by(Shipment.shipment_status)
    ).all()

    total = 0
    in_transit = 0
    delayed = 0
    delivered = 0
    status_breakdown = []

    for row in rows:
        status = row.shipment_status or "Unknown"
        count = row.count
        total += count

        if status == "Shipping":
            in_transit += count
        elif status == "Late delivery":
            delayed += count
        elif status == "Delivered":
            delivered += count

        status_breakdown.append({"status": status, "count": count})

    # Sort breakdown by count descending
    status_breakdown.sort(key=lambda x: x["count"], reverse=True)

    return {
        "total_shipments": total,
        "in_transit": in_transit,
        "delayed": delayed,
        "delivered": delivered,
        "status_breakdown": status_breakdown,
        "avg_delay_risk": 0.0,  # Will be populated in Phase 7 (ML predictions)
    }
