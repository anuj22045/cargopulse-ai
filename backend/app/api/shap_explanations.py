
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.shipment_service import get_shipment
from app.ai.ml.feature_builder import build_delay_features
from app.ai.explainability.shap_explainer import explain


router = APIRouter(
    prefix="/shipments",
    tags=["Shipment Explainability"],
)


@router.get("/{shipment_id}/explanation")
def get_shipment_explanation(
    shipment_id: int,
    db: Session = Depends(get_db),
):
    shipment = get_shipment(
        db=db,
        shipment_id=shipment_id,
    )

    if shipment is None:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    features = build_delay_features(shipment)

    try:
        result = explain(features)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "shipment_id": shipment.id,
        "explanation_method": "SHAP",
        "output_space": "raw_margin",
        "feature_importances": result["feature_importances"],
    }
