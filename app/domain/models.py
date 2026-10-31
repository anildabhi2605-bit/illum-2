"""Domain models and entity contracts for ILLUM AI STUDIO (P03-T01).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- DEC-018: Execution history retention & metadata-only policy
- DEC-019: Active project limit reduction to 4
- Single active script invariant (ACC-018)
"""

from __future__ import annotations

import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from app.domain.base import DomainBaseModel
from app.domain.constants import PROHIBITED_EXECUTION_EVENT_FIELDS
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
from app.domain.value_objects import (
    ScriptPart,
    TargetResolution,
    TokenUsage,
    ValidationReport,
)


class Project(DomainBaseModel):
    """Core project entity representing an isolated production workspace.

    Invariants:
    - project_id is unique and required for all project data scoping.
    - Aspect ratio and target resolution conform to baseline rules (ACC-008).
    - Maximum 4 active saved projects per DEC-019.
    """
    project_id: UUID
    title: str
    aspect_ratio: AspectRatio
    target_resolution: TargetResolution
    duration_seconds: float
    part_count: int
    content_language: ContentLanguage
    thumbnail_text_language: ContentLanguage
    status: ProjectStatus
    preferred_provider: Optional[str]
    preferred_model: Optional[str]
    settings_hash: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    def __init__(
        self,
        title: str,
        aspect_ratio: AspectRatio,
        target_resolution: TargetResolution,
        duration_seconds: float,
        part_count: int,
        content_language: ContentLanguage = ContentLanguage.ENGLISH,
        thumbnail_text_language: Optional[ContentLanguage] = None,
        project_id: Optional[UUID] = None,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
        settings_hash: Optional[str] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
        **extra: Any,
    ) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        resolved_project_id = project_id if project_id is not None else uuid4()
        resolved_created_at = created_at if created_at is not None else now
        resolved_updated_at = updated_at if updated_at is not None else now
        resolved_thumb_lang = thumbnail_text_language if thumbnail_text_language is not None else content_language

        if not title or not title.strip():
            raise ValueError("Project title must not be empty")

        super().__init__(
            project_id=resolved_project_id,
            title=title.strip(),
            aspect_ratio=aspect_ratio,
            target_resolution=target_resolution,
            duration_seconds=float(duration_seconds),
            part_count=int(part_count),
            content_language=content_language,
            thumbnail_text_language=resolved_thumb_lang,
            status=status,
            preferred_provider=preferred_provider,
            preferred_model=preferred_model,
            settings_hash=settings_hash,
            created_at=resolved_created_at,
            updated_at=resolved_updated_at,
            **extra,
        )


class SourceVersion(DomainBaseModel):
    """Source material version record (ACC-013, ACC-014, ACC-015).

    Invariants:
    - Meaningful source edits increment source_version and mark downstream outputs stale.
    """
    source_id: UUID
    project_id: UUID
    source_version: int
    title: str
    source_type: SourceType
    url: Optional[str]
    saved_content: str
    content_hash: str
    status: SourceStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime

    def __init__(
        self,
        project_id: UUID,
        title: str,
        source_type: SourceType,
        saved_content: str,
        content_hash: str,
        source_id: Optional[UUID] = None,
        source_version: int = 1,
        url: Optional[str] = None,
        status: SourceStatus = SourceStatus.UNVALIDATED,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
        **extra: Any,
    ) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        super().__init__(
            source_id=source_id if source_id is not None else uuid4(),
            project_id=project_id,
            source_version=source_version,
            title=title,
            source_type=source_type,
            url=url,
            saved_content=saved_content,
            content_hash=content_hash,
            status=status,
            created_at=created_at if created_at is not None else now,
            updated_at=updated_at if updated_at is not None else now,
            **extra,
        )


class Analysis(DomainBaseModel):
    """Source or Script cached analysis result."""
    analysis_id: UUID
    project_id: UUID
    analysis_type: AnalysisType
    input_hash: str
    output_payload: dict[str, Any]
    status: AnalysisStatus
    created_at: datetime.datetime

    def __init__(
        self,
        project_id: UUID,
        analysis_type: AnalysisType,
        input_hash: str,
        output_payload: dict[str, Any],
        analysis_id: Optional[UUID] = None,
        status: AnalysisStatus = AnalysisStatus.VALID,
        created_at: Optional[datetime.datetime] = None,
        **extra: Any,
    ) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        super().__init__(
            analysis_id=analysis_id if analysis_id is not None else uuid4(),
            project_id=project_id,
            analysis_type=analysis_type,
            input_hash=input_hash,
            output_payload=output_payload,
            status=status,
            created_at=created_at if created_at is not None else now,
            **extra,
        )


class ScriptCurrent(DomainBaseModel):
    """The single active script for a project (ACC-017, ACC-018).

    Strict Negative Invariant:
    - Only the latest validated script is stored per project.
    - Zero script-history tables or historical script records exist.
    """
    script_id: UUID
    project_id: UUID
    title: str
    parts: list[ScriptPart]
    content_hash: str
    source_version_used: int
    settings_hash: str
    validation_report: ValidationReport
    created_at: datetime.datetime
    updated_at: datetime.datetime

    def __init__(
        self,
        project_id: UUID,
        title: str,
        parts: list[ScriptPart],
        content_hash: str,
        source_version_used: int,
        settings_hash: str,
        validation_report: ValidationReport,
        script_id: Optional[UUID] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
        **extra: Any,
    ) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        if not parts:
            raise ValueError("ScriptCurrent must contain at least one ScriptPart")
        super().__init__(
            script_id=script_id if script_id is not None else uuid4(),
            project_id=project_id,
            title=title,
            parts=parts,
            content_hash=content_hash,
            source_version_used=source_version_used,
            settings_hash=settings_hash,
            validation_report=validation_report,
            created_at=created_at if created_at is not None else now,
            updated_at=updated_at if updated_at is not None else now,
            **extra,
        )


class Approval(DomainBaseModel):
    """User approval gate locking a specific script and settings hash (ACC-019, ACC-020).

    Invariants:
    - Any edit or regeneration of the script invalidates approval (approved = False).
    """
    approval_id: UUID
    project_id: UUID
    script_hash: str
    settings_hash: str
    status: ApprovalStatus
    is_approved: bool
    approved_at: Optional[datetime.datetime]
    approver_note: Optional[str]

    def __init__(
        self,
        project_id: UUID,
        script_hash: str,
        settings_hash: str,
        approval_id: Optional[UUID] = None,
        status: ApprovalStatus = ApprovalStatus.DRAFT,
        is_approved: bool = False,
        approved_at: Optional[datetime.datetime] = None,
        approver_note: Optional[str] = None,
        **extra: Any,
    ) -> None:
        super().__init__(
            approval_id=approval_id if approval_id is not None else uuid4(),
            project_id=project_id,
            script_hash=script_hash,
            settings_hash=settings_hash,
            status=status,
            is_approved=is_approved,
            approved_at=approved_at,
            approver_note=approver_note,
            **extra,
        )


class GeneratedOutput(DomainBaseModel):
    """Downstream generated output (Skill B Video Prompts, Skill C Thumbnail, Skill D SEO).

    Invariants:
    - Gated behind active script approval (ACC-019, ACC-020).
    - Source edit or script change marks status STALE (ACC-015, ACC-022).
    """
    output_id: UUID
    project_id: UUID
    kind: OutputKind
    input_script_hash: str
    settings_hash: str
    content: dict[str, Any]
    validation_report: ValidationReport
    status: OutputStatus
    created_at: datetime.datetime

    def __init__(
        self,
        project_id: UUID,
        kind: OutputKind,
        input_script_hash: str,
        settings_hash: str,
        content: dict[str, Any],
        validation_report: ValidationReport,
        output_id: Optional[UUID] = None,
        status: OutputStatus = OutputStatus.FRESH,
        created_at: Optional[datetime.datetime] = None,
        **extra: Any,
    ) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        super().__init__(
            output_id=output_id if output_id is not None else uuid4(),
            project_id=project_id,
            kind=kind,
            input_script_hash=input_script_hash,
            settings_hash=settings_hash,
            content=content,
            validation_report=validation_report,
            status=status,
            created_at=created_at if created_at is not None else now,
            **extra,
        )


class ExecutionEvent(DomainBaseModel):
    """Operational telemetry event for job execution history (P06-T04, DEC-018).

    MANDATORY INVARIANTS PER DEC-018:
    1. Metadata Only: Stores timestamps, latency, status, attempt count, token usage,
       provider/model, sanitized error code/type, and user fallback consent.
    2. Strict Negative Invariant: NEVER persists raw prompts, raw source text, or
       raw LLM request/response payloads.
    3. Retention Cap: Retains latest 100 records per project with FIFO pruning.
    """
    event_id: UUID
    project_id: UUID
    job_id: UUID
    skill_id: SkillIdentifier
    status: JobStatus
    provider_id: str
    model_id: str
    attempt_count: int
    created_at: datetime.datetime
    started_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]
    duration_ms: Optional[float]
    error_code: Optional[str]
    error_category: Optional[str] = None
    sanitized_error_message: Optional[str]
    token_usage: Optional[TokenUsage]
    fallback_reason: Optional[str]
    user_permission_granted: Optional[bool]

    def __init__(
        self,
        project_id: UUID,
        skill_id: SkillIdentifier,
        status: JobStatus,
        provider_id: str,
        model_id: str,
        event_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
        attempt_count: int = 1,
        created_at: Optional[datetime.datetime] = None,
        started_at: Optional[datetime.datetime] = None,
        completed_at: Optional[datetime.datetime] = None,
        duration_ms: Optional[float] = None,
        error_code: Optional[str] = None,
        error_category: Optional[str] = None,
        sanitized_error_message: Optional[str] = None,
        token_usage: Optional[TokenUsage] = None,
        fallback_reason: Optional[str] = None,
        user_permission_granted: Optional[bool] = None,
        **extra: Any,
    ) -> None:
        # DEC-018 Strict enforcement: Reject any raw prompt, source, or request/response payload
        prohibited_keys = PROHIBITED_EXECUTION_EVENT_FIELDS.intersection(extra.keys())
        if prohibited_keys:
            sorted_prohibited = sorted(prohibited_keys)
            raise ValueError(
                f"DEC-018 Security Invariant Violation: ExecutionEvent strictly forbids "
                f"raw prompt, source text, or request/response payload fields: {sorted_prohibited}"
            )

        now = datetime.datetime.now(datetime.timezone.utc)
        super().__init__(
            event_id=event_id if event_id is not None else uuid4(),
            project_id=project_id,
            job_id=job_id if job_id is not None else uuid4(),
            skill_id=skill_id,
            status=status,
            provider_id=provider_id,
            model_id=model_id,
            attempt_count=attempt_count,
            created_at=created_at if created_at is not None else now,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            error_code=error_code,
            error_category=error_category,
            sanitized_error_message=sanitized_error_message,
            token_usage=token_usage,
            fallback_reason=fallback_reason,
            user_permission_granted=user_permission_granted,
            **extra,
        )
