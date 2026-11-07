"""coupons table (M4)."""
from alembic import op
from app.database import Base
import app.models  # noqa: F401

revision = "0003_coupons"
down_revision = "0002_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["coupons"].create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["coupons"].drop(bind, checkfirst=True)
