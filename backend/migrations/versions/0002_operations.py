"""Account revocation and distinct document notifications."""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"


def upgrade():
    op.add_column(
        "users",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "deliveries",
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade():
    op.drop_column("deliveries", "payload")
    op.drop_column("users", "active")
