"""M5-M7 tables: session_messages, notifications, app_releases, bug_reports, business_config."""
from alembic import op
from app.database import Base
import app.models  # noqa: F401

revision = "0004_remote_admin"
down_revision = "0003_coupons"
branch_labels = None
depends_on = None

TABLES = ["session_messages", "notifications", "app_releases", "bug_reports", "business_config"]


def upgrade() -> None:
    bind = op.get_bind()
    for t in TABLES:
        Base.metadata.tables[t].create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for t in TABLES:
        Base.metadata.tables[t].drop(bind, checkfirst=True)
