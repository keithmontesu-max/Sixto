"""push_tokens table (M8+)."""
from alembic import op
from app.database import Base
import app.models  # noqa: F401

revision = "0006_push_tokens"
down_revision = "0005_notif_prefs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.tables["push_tokens"].create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.tables["push_tokens"].drop(op.get_bind(), checkfirst=True)
