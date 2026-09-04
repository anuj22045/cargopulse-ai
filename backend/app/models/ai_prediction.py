from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

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

    delay_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    predicted_eta: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    prediction_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )

    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    shipment = relationship(
        "Shipment",
        back_populates="predictions"
    )