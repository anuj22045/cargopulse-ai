from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

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

    recommended_action: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    expected_delay_reduction: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    expected_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    shipment = relationship(
        "Shipment",
        back_populates="recommendations"
    )
    decisions = relationship(
        "DecisionHistory",
        back_populates="recommendation"
    )