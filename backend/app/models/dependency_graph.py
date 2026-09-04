from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DependencyGraph(Base):
    __tablename__ = "dependency_graph"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    source_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    target_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    target_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    relationship_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )