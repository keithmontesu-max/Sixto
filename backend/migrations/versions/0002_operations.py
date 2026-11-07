"""device_operations table (M3)."""
from alembic import op
from app.database import Base
import app.models  # noqa: F401

revision = "0002_operations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Create only the new table (models.Base already exists from 0001).
    Base.metadata.tables["device_operations"].create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.tables["device_operations"].drop(bind, checkfirst=True)
