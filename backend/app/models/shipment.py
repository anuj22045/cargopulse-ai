from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id:Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    shipment_reference : Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    order_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    carrier_id : Mapped[int | None] = mapped_column(
        ForeignKey("carriers.id"),
        nullable=True
    )

    route_id : Mapped[int | None] = mapped_column(
        ForeignKey("routes.id"),
        nullable=True
    )

    shipping_mode : Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    shipment_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    customer_segment : Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    market:Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    order_region : Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    sales: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    profit_per_order : Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    quantity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    scheduled_shipping_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    current_latitude:Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    current_longitude : Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        onupdate = datetime.utcnow,
        nullable=False
    )

    total_distance_km: Mapped[float | None] = mapped_column(
    Float,
    nullable=True
    )

    distance_remaining_km: Mapped[float | None] = mapped_column(
    Float,
    nullable=True
    )

    simulation_elapsed_minutes: Mapped[int] = mapped_column(
    Integer,
    default=0,
    nullable=False
    )

    simulation_enabled: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    nullable=False
    )

    carrier = relationship(
        "Carrier",
        back_populates = "shipments"
    )

    route=relationship(
        "Route",
        back_populates = "shipments"
    )

    events = relationship(
        "ShipmentEvent",
        back_populates="shipment"
    )

    predictions = relationship(
        "AIPrediction",
        back_populates="shipment"
    )

    simulation_events = relationship(
        "SimulationEvent",
        back_populates="shipment"
    )

    recommendations = relationship(
        "AIRecommendation",
        back_populates="shipment"
    )

    decisions = relationship(
        "DecisionHistory",
        back_populates="shipment"
    )

    notifications = relationship(
        "Notification",
        back_populates="shipment"
    )
    documents = relationship(
        "Document",
        back_populates="shipment"
    )