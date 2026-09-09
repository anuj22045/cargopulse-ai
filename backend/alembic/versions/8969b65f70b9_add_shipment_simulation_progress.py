"""add shipment simulation progress

Revision ID: 8969b65f70b9
Revises: 456b876f374b
Create Date: 2026-09-09 11:38:29.571892

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8969b65f70b9"
down_revision: Union[str, Sequence[str], None] = "456b876f374b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "shipments",
        sa.Column(
            "total_distance_km",
            sa.Float(),
            nullable=True
        )
    )

    op.add_column(
        "shipments",
        sa.Column(
            "distance_remaining_km",
            sa.Float(),
            nullable=True
        )
    )

    op.add_column(
        "shipments",
        sa.Column(
            "simulation_elapsed_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0"
        )
    )

    op.alter_column(
        "shipments",
        "simulation_elapsed_minutes",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "shipments",
        "simulation_elapsed_minutes"
    )

    op.drop_column(
        "shipments",
        "distance_remaining_km"
    )

    op.drop_column(
        "shipments",
        "total_distance_km"
    )