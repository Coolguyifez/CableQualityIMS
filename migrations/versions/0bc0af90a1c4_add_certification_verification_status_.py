
"""Add certification verification status to raw material inspection items

Revision ID: 0bc0af90a1c4
Revises: b60a97089584
Create Date: 2026-11-22 19:13:38.835043
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0bc0af90a1c4'
down_revision = 'b60a97089584'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        'raw_material_inspection_items',
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                'certification_status',
                sa.String(length=50),
                nullable=False,
                server_default='Certification Not Verified'
            )
        )


def downgrade():
    with op.batch_alter_table(
        'raw_material_inspection_items',
        schema=None
    ) as batch_op:

        batch_op.drop_column('certification_status')
