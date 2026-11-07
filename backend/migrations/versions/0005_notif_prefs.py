"""M8+: user notification prefs columns."""
from alembic import op
import sqlalchemy as sa

revision = "0005_notif_prefs"
down_revision = "0004_remote_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ntf_order", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("users", sa.Column("ntf_payment", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("users", sa.Column("ntf_promo", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("users", sa.Column("ntf_security", sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade() -> None:
    op.drop_column("users", "ntf_security")
    op.drop_column("users", "ntf_promo")
    op.drop_column("users", "ntf_payment")
    op.drop_column("users", "ntf_order")
