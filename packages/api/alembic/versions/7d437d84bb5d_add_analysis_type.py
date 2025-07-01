"""add_analysis_type

Revision ID: 7d437d84bb5d
Revises:
Create Date: 2025-05-12 17:33:17.085685

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d437d84bb5d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add analysis_type column to analysis_tasks table
    op.add_column("analysis_tasks", sa.Column("analysis_type", sa.String(10), nullable=True))

    # Add analysis_type column to reports table
    op.add_column("reports", sa.Column("analysis_type", sa.String(10), nullable=True))

    # Update existing records to set default value "fast"
    op.execute("UPDATE analysis_tasks SET analysis_type = 'fast' WHERE analysis_type IS NULL")
    op.execute("UPDATE reports SET analysis_type = 'fast' WHERE analysis_type IS NULL")


def downgrade() -> None:
    # Remove analysis_type column from both tables
    op.drop_column("analysis_tasks", "analysis_type")
    op.drop_column("reports", "analysis_type")
