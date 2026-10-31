"""Database models, table schemas, and domain mapping for ILLUM AI STUDIO (P03-T02).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- ADR-001: SQLite local database with SQLAlchemy 2.0 declarative models
- DEC-018: Execution history metadata-only, triple CHECK constraints, cascade deletion
- DEC-019: Schema support for active project tracking
- ACC-018: Single active script table with UNIQUE constraint
"""

from __future__ import annotations

import datetime
import json
from typing import Any, Optional
from uuid import UUID

try:
    from sqlalchemy import (
        Boolean,
        CheckConstraint,
        DateTime,
        Float,
        ForeignKey,
        Index,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

    class DeclarativeBase:  # type: ignore[no-redef]
        metadata = None

    class _ColumnStub:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    Mapped = Any  # type: ignore[assignment,misc]
    mapped_column = _ColumnStub  # type: ignore[assignment]
    relationship = _ColumnStub  # type: ignore[assignment]
    CheckConstraint = _ColumnStub  # type: ignore[assignment]
    Index = _ColumnStub  # type: ignore[assignment]
    ForeignKey = _ColumnStub  # type: ignore[assignment]
    String = Text = Integer = Float = Boolean = DateTime = _ColumnStub  # type: ignore[assignment]


from app.domain.enums import (
    AnalysisStatus,
    AnalysisType,
    ApprovalStatus,
    AspectRatio,
    ContentLanguage,
    JobStatus,
    OutputKind,
    OutputStatus,
    ProjectStatus,
    SkillIdentifier,
    SourceStatus,
    SourceType,
)
from app.domain.models import (
    Analysis,
    Approval,
    ExecutionEvent,
    GeneratedOutput,
    Project,
    ScriptCurrent,
    SourceVersion,
)
from app.domain.value_objects import (
    ScriptPart,
    TargetResolution,
    TokenUsage,
    ValidationReport,
)

# Standardized allowlists for DEC-018 metadata enforcement
ALLOWED_ERROR_CATEGORIES = (
    "AUTHENTICATION",
    "RATE_LIMIT",
    "NETWORK",
    "SCHEMA_VALIDATION",
    "PROVIDER_ERROR",
    "SYSTEM_ERROR",
)

ALLOWED_ERROR_CODES = (
    "HTTP_401",
    "HTTP_403",
    "HTTP_404",
    "HTTP_429",
    "HTTP_500",
    "HTTP_502",
    "HTTP_503",
    "HTTP_504",
    "TIMEOUT",
    "CONNECTION_FAILED",
    "INVALID_JSON",
    "SCHEMA_MISMATCH",
    "INTERNAL_EXCEPTION",
)

ALLOWED_FALLBACK_REASONS = (
    "PRIMARY_PROVIDER_RATE_LIMITED",
    "PRIMARY_PROVIDER_UNAVAILABLE",
    "PRIMARY_PROVIDER_TIMEOUT",
    "PRIMARY_MODEL_QUOTA_EXCEEDED",
    "USER_REQUESTED_ALTERNATIVE",
)

# Canonical SQLite DDL reflecting all 7 tables, constraints, and indexes
SCHEMA_SQL_DDL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id CHAR(36) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    aspect_ratio VARCHAR(10) NOT NULL,
    target_width INTEGER NOT NULL,
    target_height INTEGER NOT NULL,
    duration_seconds FLOAT NOT NULL,
    part_count INTEGER NOT NULL,
    content_language VARCHAR(10) NOT NULL,
    thumbnail_text_language VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    preferred_provider VARCHAR(50) NULL,
    preferred_model VARCHAR(100) NULL,
    settings_hash VARCHAR(64) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS source_versions (
    source_id CHAR(36) PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    source_version INTEGER NOT NULL DEFAULT 1,
    title VARCHAR(200) NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    url TEXT NULL,
    saved_content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'unvalidated',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analyses (
    analysis_id CHAR(36) PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    analysis_type VARCHAR(20) NOT NULL,
    input_hash VARCHAR(64) NOT NULL,
    output_payload TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'valid',
    created_at DATETIME NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS current_scripts (
    script_id CHAR(36) PRIMARY KEY,
    project_id CHAR(36) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    parts_json TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    source_version_used INTEGER NOT NULL,
    settings_hash VARCHAR(64) NOT NULL,
    validation_report_json TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id CHAR(36) PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    script_hash VARCHAR(64) NOT NULL,
    settings_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    is_approved BOOLEAN NOT NULL DEFAULT 0,
    approved_at DATETIME NULL,
    approver_note TEXT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generated_outputs (
    output_id CHAR(36) PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    kind VARCHAR(30) NOT NULL,
    input_script_hash VARCHAR(64) NOT NULL,
    settings_hash VARCHAR(64) NOT NULL,
    content_json TEXT NOT NULL,
    validation_report_json TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'fresh',
    created_at DATETIME NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS execution_events (
    event_id CHAR(36) PRIMARY KEY,
    project_id CHAR(36) NOT NULL,
    job_id CHAR(36) NOT NULL,
    skill_id VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    provider_id VARCHAR(50) NOT NULL,
    model_id VARCHAR(100) NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    duration_ms FLOAT NULL,
    error_code VARCHAR(50) NULL,
    error_category VARCHAR(50) NULL,
    tokens_in INTEGER NULL,
    tokens_out INTEGER NULL,
    tokens_total INTEGER NULL,
    fallback_reason VARCHAR(50) NULL,
    user_permission_granted BOOLEAN NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    CONSTRAINT chk_error_category CHECK (
        error_category IS NULL OR error_category IN (
            'AUTHENTICATION',
            'RATE_LIMIT',
            'NETWORK',
            'SCHEMA_VALIDATION',
            'PROVIDER_ERROR',
            'SYSTEM_ERROR'
        )
    ),
    CONSTRAINT chk_error_code CHECK (
        error_code IS NULL OR error_code IN (
            'HTTP_401',
            'HTTP_403',
            'HTTP_404',
            'HTTP_429',
            'HTTP_500',
            'HTTP_502',
            'HTTP_503',
            'HTTP_504',
            'TIMEOUT',
            'CONNECTION_FAILED',
            'INVALID_JSON',
            'SCHEMA_MISMATCH',
            'INTERNAL_EXCEPTION'
        )
    ),
    CONSTRAINT chk_fallback_reason CHECK (
        fallback_reason IS NULL OR fallback_reason IN (
            'PRIMARY_PROVIDER_RATE_LIMITED',
            'PRIMARY_PROVIDER_UNAVAILABLE',
            'PRIMARY_PROVIDER_TIMEOUT',
            'PRIMARY_MODEL_QUOTA_EXCEEDED',
            'USER_REQUESTED_ALTERNATIVE'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_sources_project_version ON source_versions(project_id, source_version);
CREATE INDEX IF NOT EXISTS idx_analyses_project_type_hash ON analyses(project_id, analysis_type, input_hash);
CREATE INDEX IF NOT EXISTS idx_approvals_project_hash ON approvals(project_id, script_hash, settings_hash);
CREATE INDEX IF NOT EXISTS idx_outputs_project_kind ON generated_outputs(project_id, kind);
CREATE INDEX IF NOT EXISTS idx_execution_events_project_created ON execution_events(project_id, created_at DESC);
"""


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Declarative Base."""
    pass


class ProjectModel(Base):
    """SQLAlchemy model for projects table."""
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(10), nullable=False)
    target_width: Mapped[int] = mapped_column(Integer, nullable=False)
    target_height: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    part_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content_language: Mapped[str] = mapped_column(String(10), nullable=False)
    thumbnail_text_language: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    preferred_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    settings_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_projects_status", "status"),
    )

    # Relationships with cascade deletion
    sources: Mapped[list["SourceVersionModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["AnalysisModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    current_script: Mapped[Optional["CurrentScriptModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    approvals: Mapped[list["ApprovalModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    outputs: Mapped[list["GeneratedOutputModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    execution_events: Mapped[list["ExecutionEventModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    def to_domain(self) -> Project:
        return Project(
            project_id=UUID(self.project_id),
            title=self.title,
            aspect_ratio=AspectRatio(self.aspect_ratio),
            target_resolution=TargetResolution(width=self.target_width, height=self.target_height),
            duration_seconds=self.duration_seconds,
            part_count=self.part_count,
            content_language=ContentLanguage(self.content_language),
            thumbnail_text_language=ContentLanguage(self.thumbnail_text_language),
            status=ProjectStatus(self.status),
            preferred_provider=self.preferred_provider,
            preferred_model=self.preferred_model,
            settings_hash=self.settings_hash,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class SourceVersionModel(Base):
    """SQLAlchemy model for source_versions table."""
    __tablename__ = "source_versions"

    source_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    source_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    saved_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unvalidated")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_sources_project_version", "project_id", "source_version"),
    )

    project: Mapped["ProjectModel"] = relationship(back_populates="sources")

    def to_domain(self) -> SourceVersion:
        return SourceVersion(
            source_id=UUID(self.source_id),
            project_id=UUID(self.project_id),
            source_version=self.source_version,
            title=self.title,
            source_type=SourceType(self.source_type),
            url=self.url,
            saved_content=self.saved_content,
            content_hash=self.content_hash,
            status=SourceStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class AnalysisModel(Base):
    """SQLAlchemy model for analyses table."""
    __tablename__ = "analyses"

    analysis_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(20), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    output_payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="valid")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_analyses_project_type_hash", "project_id", "analysis_type", "input_hash"),
    )

    project: Mapped["ProjectModel"] = relationship(back_populates="analyses")

    def to_domain(self) -> Analysis:
        return Analysis(
            analysis_id=UUID(self.analysis_id),
            project_id=UUID(self.project_id),
            analysis_type=AnalysisType(self.analysis_type),
            input_hash=self.input_hash,
            output_payload=json.loads(self.output_payload),
            status=AnalysisStatus(self.status),
            created_at=self.created_at,
        )


class CurrentScriptModel(Base):
    """SQLAlchemy model for current_scripts table (Single Active Script - ACC-018)."""
    __tablename__ = "current_scripts"

    script_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    parts_json: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_version_used: Mapped[int] = mapped_column(Integer, nullable=False)
    settings_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    validation_report_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    project: Mapped["ProjectModel"] = relationship(back_populates="current_script")

    def to_domain(self) -> ScriptCurrent:
        raw_parts = json.loads(self.parts_json)
        parts = [ScriptPart(**p) for p in raw_parts]
        raw_report = json.loads(self.validation_report_json)
        report = ValidationReport(**raw_report)
        return ScriptCurrent(
            script_id=UUID(self.script_id),
            project_id=UUID(self.project_id),
            title=self.title,
            parts=parts,
            content_hash=self.content_hash,
            source_version_used=self.source_version_used,
            settings_hash=self.settings_hash,
            validation_report=report,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ApprovalModel(Base):
    """SQLAlchemy model for approvals table."""
    __tablename__ = "approvals"

    approval_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    script_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    settings_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    approver_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_approvals_project_hash", "project_id", "script_hash", "settings_hash"),
    )

    project: Mapped["ProjectModel"] = relationship(back_populates="approvals")

    def to_domain(self) -> Approval:
        return Approval(
            approval_id=UUID(self.approval_id),
            project_id=UUID(self.project_id),
            script_hash=self.script_hash,
            settings_hash=self.settings_hash,
            status=ApprovalStatus(self.status),
            is_approved=self.is_approved,
            approved_at=self.approved_at,
            approver_note=self.approver_note,
        )


class GeneratedOutputModel(Base):
    """SQLAlchemy model for generated_outputs table."""
    __tablename__ = "generated_outputs"

    output_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    input_script_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    settings_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    validation_report_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="fresh")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_outputs_project_kind", "project_id", "kind"),
    )

    project: Mapped["ProjectModel"] = relationship(back_populates="outputs")

    def to_domain(self) -> GeneratedOutput:
        return GeneratedOutput(
            output_id=UUID(self.output_id),
            project_id=UUID(self.project_id),
            kind=OutputKind(self.kind),
            input_script_hash=self.input_script_hash,
            settings_hash=self.settings_hash,
            content=json.loads(self.content_json),
            validation_report=ValidationReport(**json.loads(self.validation_report_json)),
            status=OutputStatus(self.status),
            created_at=self.created_at,
        )


class ExecutionEventModel(Base):
    """SQLAlchemy model for execution_events table (DEC-018: Metadata Only)."""
    __tablename__ = "execution_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fallback_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_permission_granted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    __table_args__ = (
        Index("idx_execution_events_project_created", "project_id", "created_at"),
        CheckConstraint(
            "error_category IS NULL OR error_category IN ("
            "'AUTHENTICATION', 'RATE_LIMIT', 'NETWORK', 'SCHEMA_VALIDATION', 'PROVIDER_ERROR', 'SYSTEM_ERROR')",
            name="chk_error_category",
        ),
        CheckConstraint(
            "error_code IS NULL OR error_code IN ("
            "'HTTP_401', 'HTTP_403', 'HTTP_404', 'HTTP_429', 'HTTP_500', 'HTTP_502', 'HTTP_503', 'HTTP_504', "
            "'TIMEOUT', 'CONNECTION_FAILED', 'INVALID_JSON', 'SCHEMA_MISMATCH', 'INTERNAL_EXCEPTION')",
            name="chk_error_code",
        ),
        CheckConstraint(
            "fallback_reason IS NULL OR fallback_reason IN ("
            "'PRIMARY_PROVIDER_RATE_LIMITED', 'PRIMARY_PROVIDER_UNAVAILABLE', 'PRIMARY_PROVIDER_TIMEOUT', "
            "'PRIMARY_MODEL_QUOTA_EXCEEDED', 'USER_REQUESTED_ALTERNATIVE')",
            name="chk_fallback_reason",
        ),
    )

    project: Mapped["ProjectModel"] = relationship(back_populates="execution_events")

    def to_domain(self) -> ExecutionEvent:
        token_usage = None
        if self.tokens_in is not None or self.tokens_out is not None or self.tokens_total is not None:
            token_usage = TokenUsage(
                prompt_tokens=self.tokens_in or 0,
                completion_tokens=self.tokens_out or 0,
                total_tokens=self.tokens_total or 0,
            )

        return ExecutionEvent(
            event_id=UUID(self.event_id),
            project_id=UUID(self.project_id),
            job_id=UUID(self.job_id),
            skill_id=SkillIdentifier(self.skill_id),
            status=JobStatus(self.status),
            provider_id=self.provider_id,
            model_id=self.model_id,
            attempt_count=self.attempt_count,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            duration_ms=self.duration_ms,
            error_code=self.error_code,
            token_usage=token_usage,
            fallback_reason=self.fallback_reason,
            user_permission_granted=self.user_permission_granted,
        )
