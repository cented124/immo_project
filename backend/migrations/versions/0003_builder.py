"""Builder configuration history."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"


def upgrade():
    op.create_table(
        "revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.String(254), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("revisions")
