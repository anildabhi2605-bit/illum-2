"""Initial SQLite schema: 7 core tables, constraints, and indexes (P03-T02).

Revision ID: 001
Revises: None
Create Date: 2026-10-31 00:00:00.000000

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- DEC-018: execution_events metadata only with triple check constraints
- ACC-018: current_scripts UNIQUE(project_id)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. projects
    op.create_table(
        "projects",
        sa.Column("project_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("aspect_ratio", sa.String(length=10), nullable=False),
        sa.Column("target_width", sa.Integer(), nullable=False),
        sa.Column("target_height", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("part_count", sa.Integer(), nullable=False),
        sa.Column("content_language", sa.String(length=10), nullable=False),
        sa.Column("thumbnail_text_language", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("preferred_provider", sa.String(length=50), nullable=True),
        sa.Column("preferred_model", sa.String(length=100), nullable=True),
        sa.Column("settings_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_projects_status", "projects", ["status"])

    # 2. source_versions
    op.create_table(
        "source_versions",
        sa.Column("source_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("saved_content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="unvalidated", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_sources_project_version", "source_versions", ["project_id", "source_version"])

    # 3. analyses
    op.create_table(
        "analyses",
        sa.Column("analysis_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_type", sa.String(length=20), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("output_payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="valid", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_analyses_project_type_hash", "analyses", ["project_id", "analysis_type", "input_hash"])

    # 4. current_scripts (ACC-018: Unique project_id)
    op.create_table(
        "current_scripts",
        sa.Column("script_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.project_id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("parts_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_version_used", sa.Integer(), nullable=False),
        sa.Column("settings_hash", sa.String(length=64), nullable=False),
        sa.Column("validation_report_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 5. approvals
    op.create_table(
        "approvals",
        sa.Column("approval_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("script_hash", sa.String(length=64), nullable=False),
        sa.Column("settings_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("is_approved", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approver_note", sa.Text(), nullable=True),
    )
    op.create_index("idx_approvals_project_hash", "approvals", ["project_id", "script_hash", "settings_hash"])

    # 6. generated_outputs
    op.create_table(
        "generated_outputs",
        sa.Column("output_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("input_script_hash", sa.String(length=64), nullable=False),
        sa.Column("settings_hash", sa.String(length=64), nullable=False),
        sa.Column("content_json", sa.Text(), nullable=False),
        sa.Column("validation_report_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="fresh", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_outputs_project_kind", "generated_outputs", ["project_id", "kind"])

    # 7. execution_events (DEC-018: Metadata only with triple check constraints)
    op.create_table(
        "execution_events",
        sa.Column("event_id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("skill_id", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provider_id", sa.String(length=50), nullable=False),
        sa.Column("model_id", sa.String(length=100), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_category", sa.String(length=50), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("tokens_total", sa.Integer(), nullable=True),
        sa.Column("fallback_reason", sa.String(length=50), nullable=True),
        sa.Column("user_permission_granted", sa.Boolean(), nullable=True),
        sa.CheckConstraint(
            "error_category IS NULL OR error_category IN ("
            "'AUTHENTICATION', 'RATE_LIMIT', 'NETWORK', 'SCHEMA_VALIDATION', 'PROVIDER_ERROR', 'SYSTEM_ERROR')",
            name="chk_error_category",
        ),
        sa.CheckConstraint(
            "error_code IS NULL OR error_code IN ("
            "'HTTP_401', 'HTTP_403', 'HTTP_404', 'HTTP_429', 'HTTP_500', 'HTTP_502', 'HTTP_503', 'HTTP_504', "
            "'TIMEOUT', 'CONNECTION_FAILED', 'INVALID_JSON', 'SCHEMA_MISMATCH', 'INTERNAL_EXCEPTION')",
            name="chk_error_code",
        ),
        sa.CheckConstraint(
            "fallback_reason IS NULL OR fallback_reason IN ("
            "'PRIMARY_PROVIDER_RATE_LIMITED', 'PRIMARY_PROVIDER_UNAVAILABLE', 'PRIMARY_PROVIDER_TIMEOUT', "
            "'PRIMARY_MODEL_QUOTA_EXCEEDED', 'USER_REQUESTED_ALTERNATIVE')",
            name="chk_fallback_reason",
        ),
    )
    op.create_index("idx_execution_events_project_created", "execution_events", ["project_id", "created_at"])


def downgrade() -> None:
    op.drop_table("execution_events")
    op.drop_table("generated_outputs")
    op.drop_table("approvals")
    op.drop_table("current_scripts")
    op.drop_table("analyses")
    op.drop_table("source_versions")
    op.drop_table("projects")
