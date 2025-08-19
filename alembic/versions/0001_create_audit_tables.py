from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pilots",
        sa.Column("pilot_id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ctx_id", sa.String(), nullable=True),
        sa.Column("pilot_id", sa.String(), sa.ForeignKey("pilots.pilot_id"), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_preferences_ctx_id", "preferences", ["ctx_id"])
    op.create_index("ix_preferences_pilot_id", "preferences", ["pilot_id"])

    op.create_table(
        "rule_packs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ctx_id", sa.String(), nullable=True),
        sa.Column("airline", sa.String(), nullable=True),
        sa.Column("version", sa.String(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rule_packs_ctx_id", "rule_packs", ["ctx_id"])
    op.create_index("ix_rule_packs_airline", "rule_packs", ["airline"])

    op.create_table(
        "bid_packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ctx_id", sa.String(), nullable=True),
        sa.Column("airline", sa.String(), nullable=True),
        sa.Column("month", sa.String(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_bid_packages_ctx_id", "bid_packages", ["ctx_id"])
    op.create_index("ix_bid_packages_airline", "bid_packages", ["airline"])
    op.create_index("ix_bid_packages_month", "bid_packages", ["month"])

    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ctx_id", sa.String(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_candidates_ctx_id", "candidates", ["ctx_id"])

    op.create_table(
        "exports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ctx_id", sa.String(), nullable=True),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_exports_ctx_id", "exports", ["ctx_id"])

    op.create_table(
        "audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ctx_id", sa.String(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_ctx_id", "audit", ["ctx_id"])
    op.create_index("ix_audit_stage", "audit", ["stage"])
    op.create_index("ix_audit_timestamp", "audit", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_audit_timestamp", table_name="audit")
    op.drop_index("ix_audit_stage", table_name="audit")
    op.drop_index("ix_audit_ctx_id", table_name="audit")
    op.drop_table("audit")
    op.drop_index("ix_exports_ctx_id", table_name="exports")
    op.drop_table("exports")
    op.drop_index("ix_candidates_ctx_id", table_name="candidates")
    op.drop_table("candidates")
    op.drop_index("ix_bid_packages_month", table_name="bid_packages")
    op.drop_index("ix_bid_packages_airline", table_name="bid_packages")
    op.drop_index("ix_bid_packages_ctx_id", table_name="bid_packages")
    op.drop_table("bid_packages")
    op.drop_index("ix_rule_packs_airline", table_name="rule_packs")
    op.drop_index("ix_rule_packs_ctx_id", table_name="rule_packs")
    op.drop_table("rule_packs")
    op.drop_index("ix_preferences_pilot_id", table_name="preferences")
    op.drop_index("ix_preferences_ctx_id", table_name="preferences")
    op.drop_table("preferences")
    op.drop_table("pilots")
