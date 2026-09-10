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

    # ── Weather condition at the time of the tick ──────────────────
    weather: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # ── Port / road congestion level ───────────────────────────────
    congestion_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # ── Combined speed modifier (weather × congestion) ─────────────
    speed_modifier: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    # ── Extra hours added to ETA because of port congestion ────────
    port_wait_hours: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    # ── Position at tick time ──────────────────────────────────────
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