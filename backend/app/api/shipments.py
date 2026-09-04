# This file handles the HTTP/API side and calls those service functions.
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentUpdate,
)
from app.services.shipment_service import (
    get_shipment,
    get_shipments,
    create_shipment,
    update_shipment,
    delete_shipment,
)


router = APIRouter(
    prefix="/shipments",
    tags=["Shipments"]
)


@router.get(
    "/",
    response_model=list[ShipmentResponse]
)
def read_shipments(
    skip: int = 0,
    limit: int = 100,
    shipping_mode: str | None = None,
    shipment_status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    if skip < 0:
        raise HTTPException(
            status_code=400,
            detail="skip cannot be negative"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100"
        )

    return get_shipments(
        db=db,
        skip=skip,
        limit=limit,
        shipping_mode=shipping_mode,
        shipment_status=shipment_status,
        search=search
    )


@router.get(
    "/{shipment_id}",
    response_model=ShipmentResponse
)
def read_shipment(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    shipment = get_shipment(
        db=db,
        shipment_id=shipment_id
    )

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    return shipment


@router.post(
    "/",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_shipment(
    shipment_data: ShipmentCreate,
    db: Session = Depends(get_db)
):
    return create_shipment(
        db=db,
        shipment_data=shipment_data
    )


@router.put(
    "/{shipment_id}",
    response_model=ShipmentResponse
)
def update_existing_shipment(
    shipment_id: int,
    shipment_data: ShipmentUpdate,
    db: Session = Depends(get_db)
):
    shipment = update_shipment(
        db=db,
        shipment_id=shipment_id,
        shipment_data=shipment_data
    )

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    return shipment


@router.delete(
    "/{shipment_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_existing_shipment(
    shipment_id: int,
    db: Session = Depends(get_db)
):
    deleted = delete_shipment(
        db=db,
        shipment_id=shipment_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )