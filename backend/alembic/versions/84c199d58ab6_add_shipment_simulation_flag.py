"""add shipment simulation flag

Revision ID: 84c199d58ab6
Revises: 8969b65f70b9
Create Date: 2026-09-09

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "84c199d58ab6"
down_revision: Union[str, Sequence[str], None] = "8969b65f70b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "shipments",
        sa.Column(
            "simulation_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

    op.alter_column(
        "shipments",
        "simulation_enabled",
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "shipments",
        "simulation_enabled"
    )