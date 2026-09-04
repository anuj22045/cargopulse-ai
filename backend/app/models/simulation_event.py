from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SimulationEvent(Base):
    __tablename__ = "simulation_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id"),
        nullable=False,
        index=True
    )

    simulation_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )

    traffic_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    humidity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    waiting_time: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    asset_utilization: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    shipment = relationship(
        "Shipment",
        back_populates="simulation_events"
    )