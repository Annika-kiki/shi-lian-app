"""add query indexes and unique workout set numbers

Revision ID: 0002
Revises: 0001
"""
from alembic import context, op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not context.is_offline_mode():
        connection = op.get_bind()
        rows = connection.execute(sa.text(
            "SELECT session_id, set_no, MIN(id) AS keep_id FROM workout_sets "
            "GROUP BY session_id, set_no HAVING COUNT(*) > 1"
        )).mappings()
        for row in rows:
            connection.execute(sa.text(
                "DELETE FROM workout_sets WHERE session_id=:session_id "
                "AND set_no=:set_no AND id<>:keep_id"
            ), row)
    with op.batch_alter_table("workout_sets") as batch_op:
        batch_op.create_unique_constraint("uq_workout_set_number", ["session_id", "set_no"])
    op.create_index("ix_meal_user_date", "meal_records", ["user_id", "record_date"])
    op.create_index("ix_workout_user_date", "workout_sessions", ["user_id", "workout_date"])


def downgrade() -> None:
    op.drop_index("ix_workout_user_date", table_name="workout_sessions")
    op.drop_index("ix_meal_user_date", table_name="meal_records")
    with op.batch_alter_table("workout_sets") as batch_op:
        batch_op.drop_constraint("uq_workout_set_number", type_="unique")
