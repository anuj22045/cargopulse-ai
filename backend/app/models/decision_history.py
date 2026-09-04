from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DecisionHistory(Base):
    __tablename__ = "decision_history"

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

    recommendation_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_recommendations.id"),
        nullable=True,
        index=True
    )

    decision: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    decision_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    actual_outcome: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    shipment = relationship(
        "Shipment",
        back_populates="decisions"
    )

    recommendation = relationship(
        "AIRecommendation",
        back_populates="decisions"
    )