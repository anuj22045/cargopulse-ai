from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    origin: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    destination: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    route_code: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    shipments = relationship(
        "Shipment",
        back_populates="route"
    )