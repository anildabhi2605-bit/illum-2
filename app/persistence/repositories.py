"""Project-scoped persistence repositories for ILLUM AI STUDIO (P03-T03).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- DEC-018: Metadata-only execution events, allowlists, deterministic ordering
- DEC-019: Project isolation, count active, oldest query, and cascading relational deletion
- ACC-018: Single active script invariant with savepoint failure atomicity
"""

from __future__ import annotations

import datetime
import json
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.constants import PROHIBITED_EXECUTION_EVENT_FIELDS
from app.domain.enums import (
    AnalysisStatus,
    AnalysisType,
    ApprovalStatus,
    OutputKind,
    OutputStatus,
    ProjectStatus,
    SourceStatus,
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
from app.persistence.exceptions import (
    ConstraintViolationError,
    EntityNotFoundError,
    ProjectMismatchError,
)
from app.persistence.models import (
    ALLOWED_ERROR_CATEGORIES,
    ALLOWED_ERROR_CODES,
    ALLOWED_FALLBACK_REASONS,
    AnalysisModel,
    ApprovalModel,
    CurrentScriptModel,
    ExecutionEventModel,
    GeneratedOutputModel,
    ProjectModel,
    SourceVersionModel,
)


def _to_str_id(val: UUID | str) -> str:
    """Normalize UUID or string identifier to string."""
    return str(val)


class BaseRepository:
    """Base class for session-scoped repositories."""

    def __init__(self, session: Session) -> None:
        self.session = session


class ProjectRepository(BaseRepository):
    """Repository for managing the Project aggregate root."""

    def create(self, project: Project) -> Project:
        """Persist a new Project domain entity."""
        model = ProjectModel(
            project_id=str(project.project_id),
            title=project.title,
            aspect_ratio=project.aspect_ratio.value,
            target_width=project.target_resolution.width,
            target_height=project.target_resolution.height,
            duration_seconds=project.duration_seconds,
            part_count=project.part_count,
            content_language=project.content_language.value,
            thumbnail_text_language=project.thumbnail_text_language.value,
            status=project.status.value,
            preferred_provider=project.preferred_provider,
            preferred_model=project.preferred_model,
            settings_hash=project.settings_hash,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        try:
            self.session.add(model)
            self.session.flush()
        except IntegrityError as exc:
            raise ConstraintViolationError(f"Failed to create project: {exc}") from exc
        return model.to_domain()

    def get_by_id(self, project_id: UUID | str) -> Optional[Project]:
        """Retrieve project by primary key."""
        pid = _to_str_id(project_id)
        stmt = select(ProjectModel).where(ProjectModel.project_id == pid)
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def list_active(self) -> list[Project]:
        """List all projects with status == 'active' ordered by created_at DESC."""
        stmt = (
            select(ProjectModel)
            .where(ProjectModel.status == ProjectStatus.ACTIVE.value)
            .order_by(ProjectModel.created_at.desc(), ProjectModel.project_id.desc())
        )
        models = self.session.execute(stmt).scalars().all()
        return [m.to_domain() for m in models]

    def update(self, project: Project) -> Project:
        """Update an existing Project domain entity."""
        pid = str(project.project_id)
        stmt = select(ProjectModel).where(ProjectModel.project_id == pid)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            raise EntityNotFoundError(f"Project with ID '{pid}' not found.")

        model.title = project.title
        model.aspect_ratio = project.aspect_ratio.value
        model.target_width = project.target_resolution.width
        model.target_height = project.target_resolution.height
        model.duration_seconds = project.duration_seconds
        model.part_count = project.part_count
        model.content_language = project.content_language.value
        model.thumbnail_text_language = project.thumbnail_text_language.value
        model.status = project.status.value
        model.preferred_provider = project.preferred_provider
        model.preferred_model = project.preferred_model
        model.settings_hash = project.settings_hash
        model.updated_at = project.updated_at

        try:
            self.session.flush()
        except IntegrityError as exc:
            raise ConstraintViolationError(f"Failed to update project: {exc}") from exc
        return model.to_domain()

    def delete(self, project_id: UUID | str) -> bool:
        """Delete project record. Cascades to all child rows via foreign keys.
        
        Zero file or .env modifications.
        """
        pid = _to_str_id(project_id)
        stmt = select(ProjectModel).where(ProjectModel.project_id == pid)
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def count_active(self) -> int:
        """Count active projects (DEC-019 limit support)."""
        stmt = (
            select(func.count())
            .select_from(ProjectModel)
            .where(ProjectModel.status == ProjectStatus.ACTIVE.value)
        )
        return int(self.session.execute(stmt).scalar_one())

    def get_oldest_active(self) -> Optional[Project]:
        """Retrieve the oldest active project by created_at (DEC-019 replacement support)."""
        stmt = (
            select(ProjectModel)
            .where(ProjectModel.status == ProjectStatus.ACTIVE.value)
            .order_by(ProjectModel.created_at.asc(), ProjectModel.project_id.asc())
            .limit(1)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None


class SourceVersionRepository(BaseRepository):
    """Repository for managing project-scoped SourceVersion entities."""

    def create(self, project_id: UUID | str, source: SourceVersion) -> SourceVersion:
        """Create a SourceVersion explicitly verifying project_id."""
        pid = _to_str_id(project_id)
        if str(source.project_id) != pid:
            raise ProjectMismatchError(
                f"SourceVersion project_id '{source.project_id}' does not match target project_id '{pid}'."
            )

        model = SourceVersionModel(
            source_id=str(source.source_id),
            project_id=pid,
            source_version=source.source_version,
            title=source.title,
            source_type=source.source_type.value,
            url=source.url,
            saved_content=source.saved_content,
            content_hash=source.content_hash,
            status=source.status.value,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )
        try:
            self.session.add(model)
            self.session.flush()
        except IntegrityError as exc:
            raise ConstraintViolationError(f"Failed to create SourceVersion: {exc}") from exc
        return model.to_domain()

    def get_by_id(self, project_id: UUID | str, source_id: UUID | str) -> Optional[SourceVersion]:
        """Retrieve source version scoped by project_id."""
        pid = _to_str_id(project_id)
        sid = _to_str_id(source_id)
        stmt = select(SourceVersionModel).where(
            SourceVersionModel.source_id == sid,
            SourceVersionModel.project_id == pid,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def get_latest(self, project_id: UUID | str) -> Optional[SourceVersion]:
        """Retrieve latest source version for project."""
        pid = _to_str_id(project_id)
        stmt = (
            select(SourceVersionModel)
            .where(SourceVersionModel.project_id == pid)
            .order_by(SourceVersionModel.source_version.desc())
            .limit(1)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def list_by_project(self, project_id: UUID | str) -> list[SourceVersion]:
        """List all source versions for project ordered by version descending."""
        pid = _to_str_id(project_id)
        stmt = (
            select(SourceVersionModel)
            .where(SourceVersionModel.project_id == pid)
            .order_by(SourceVersionModel.source_version.desc(), SourceVersionModel.source_id.desc())
        )
        models = self.session.execute(stmt).scalars().all()
        return [m.to_domain() for m in models]

    def update_status(
        self, project_id: UUID | str, source_id: UUID | str, status: SourceStatus
    ) -> Optional[SourceVersion]:
        """Update source status within project scope."""
        pid = _to_str_id(project_id)
        sid = _to_str_id(source_id)
        stmt = select(SourceVersionModel).where(
            SourceVersionModel.source_id == sid,
            SourceVersionModel.project_id == pid,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if not model:
            return None

        model.status = status.value
        model.updated_at = datetime.datetime.now(datetime.timezone.utc)
        self.session.flush()
        return model.to_domain()


class AnalysisRepository(BaseRepository):
    """Repository for managing cached source and script analyses."""

    def create(self, project_id: UUID | str, analysis: Analysis) -> Analysis:
        """Create an Analysis record explicitly verifying project_id."""
        pid = _to_str_id(project_id)
        if str(analysis.project_id) != pid:
            raise ProjectMismatchError(
                f"Analysis project_id '{analysis.project_id}' does not match target project_id '{pid}'."
            )

        model = AnalysisModel(
            analysis_id=str(analysis.analysis_id),
            project_id=pid,
            analysis_type=analysis.analysis_type.value,
            input_hash=analysis.input_hash,
            output_payload=json.dumps(analysis.output_payload, default=str),
            status=analysis.status.value,
            created_at=analysis.created_at,
        )
        try:
            self.session.add(model)
            self.session.flush()
        except IntegrityError as exc:
            raise ConstraintViolationError(f"Failed to create Analysis: {exc}") from exc
        return model.to_domain()

    def get_by_id(self, project_id: UUID | str, analysis_id: UUID | str) -> Optional[Analysis]:
        """Retrieve analysis by ID scoped by project_id."""
        pid = _to_str_id(project_id)
        aid = _to_str_id(analysis_id)
        stmt = select(AnalysisModel).where(
            AnalysisModel.analysis_id == aid,
            AnalysisModel.project_id == pid,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def get_by_hash(
        self, project_id: UUID | str, analysis_type: AnalysisType, input_hash: str
    ) -> Optional[Analysis]:
        """Retrieve valid cached analysis for input hash within project scope."""
        pid = _to_str_id(project_id)
        stmt = (
            select(AnalysisModel)
            .where(
                AnalysisModel.project_id == pid,
                AnalysisModel.analysis_type == analysis_type.value,
                AnalysisModel.input_hash == input_hash,
                AnalysisModel.status == AnalysisStatus.VALID.value,
            )
            .order_by(AnalysisModel.created_at.desc(), AnalysisModel.analysis_id.desc())
            .limit(1)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def invalidate_for_project(
        self, project_id: UUID | str, analysis_type: Optional[AnalysisType] = None
    ) -> int:
        """Mark analyses as invalid for the project."""
        pid = _to_str_id(project_id)
        conditions = [AnalysisModel.project_id == pid, AnalysisModel.status == AnalysisStatus.VALID.value]
        if analysis_type is not None:
            conditions.append(AnalysisModel.analysis_type == analysis_type.value)

        stmt = update(AnalysisModel).where(*conditions).values(status=AnalysisStatus.INVALID.value)
        result = self.session.execute(stmt)
        self.session.flush()
        return int(result.rowcount)


class CurrentScriptRepository(BaseRepository):
    """Repository for managing the single active script with savepoint failure atomicity (ACC-018)."""

    def save_or_replace(self, project_id: UUID | str, script: ScriptCurrent) -> ScriptCurrent:
        """Atomically upsert the single active script record inside a savepoint.
        
        Guarantees that if serialization, validation, or persistence fails,
        the savepoint rolls back and the previous valid script remains intact in the session and DB.
        """
        pid = _to_str_id(project_id)
        if str(script.project_id) != pid:
            raise ProjectMismatchError(
                f"ScriptCurrent project_id '{script.project_id}' does not match target project_id '{pid}'."
            )

        with self.session.begin_nested():
            parts_payload = json.dumps([p.model_dump() for p in script.parts], default=str)
            report_payload = json.dumps(script.validation_report.model_dump(), default=str)

            stmt = select(CurrentScriptModel).where(CurrentScriptModel.project_id == pid)
            existing = self.session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.title = script.title
                existing.parts_json = parts_payload
                existing.content_hash = script.content_hash
                existing.source_version_used = script.source_version_used
                existing.settings_hash = script.settings_hash
                existing.validation_report_json = report_payload
                existing.updated_at = script.updated_at
                self.session.flush()
                return existing.to_domain()
            else:
                new_model = CurrentScriptModel(
                    script_id=str(script.script_id),
                    project_id=pid,
                    title=script.title,
                    parts_json=parts_payload,
                    content_hash=script.content_hash,
                    source_version_used=script.source_version_used,
                    settings_hash=script.settings_hash,
                    validation_report_json=report_payload,
                    created_at=script.created_at,
                    updated_at=script.updated_at,
                )
                try:
                    self.session.add(new_model)
                    self.session.flush()
                except IntegrityError as exc:
                    raise ConstraintViolationError(f"Failed to insert CurrentScript: {exc}") from exc
                return new_model.to_domain()

    def get(self, project_id: UUID | str) -> Optional[ScriptCurrent]:
        """Retrieve current script for project."""
        pid = _to_str_id(project_id)
        stmt = select(CurrentScriptModel).where(CurrentScriptModel.project_id == pid)
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def delete(self, project_id: UUID | str) -> bool:
        """Delete current script for project."""
        pid = _to_str_id(project_id)
        stmt = delete(CurrentScriptModel).where(CurrentScriptModel.project_id == pid)
        result = self.session.execute(stmt)
        self.session.flush()
        return int(result.rowcount) > 0


class ApprovalRepository(BaseRepository):
    """Repository for managing approval gate lifecycle with mandatory authoritative hash verification."""

    def create(self, project_id: UUID | str, approval: Approval) -> Approval:
        """Create an Approval entity preserving its exact domain state without silent promotion."""
        pid = _to_str_id(project_id)
        if str(approval.project_id) != pid:
            raise ProjectMismatchError(
                f"Approval project_id '{approval.project_id}' does not match target project_id '{pid}'."
            )

        model = ApprovalModel(
            approval_id=str(approval.approval_id),
            project_id=pid,
            script_hash=approval.script_hash,
            settings_hash=approval.settings_hash,
            status=approval.status.value,
            is_approved=approval.is_approved,
            approved_at=approval.approved_at,
            approver_note=approval.approver_note,
        )
        try:
            self.session.add(model)
            self.session.flush()
        except IntegrityError as exc:
            raise ConstraintViolationError(f"Failed to create Approval: {exc}") from exc
        return model.to_domain()

    def get_current(
        self, project_id: UUID | str, current_script_hash: str, current_settings_hash: str
    ) -> Optional[Approval]:
        """Retrieve active approval verifying caller hashes against database-authoritative records.
        
        Ordered by existing schema columns: approved_at DESC, approval_id DESC.
        Returns None if caller hashes are stale, missing, or mismatched.
        """
        pid = _to_str_id(project_id)
        if not current_script_hash or not current_settings_hash:
            return None

        # 1. Authoritative DB verification for CurrentScript
        script_stmt = select(CurrentScriptModel).where(CurrentScriptModel.project_id == pid)
        script_model = self.session.execute(script_stmt).scalar_one_or_none()
        if not script_model or script_model.content_hash != current_script_hash:
            return None

        # 2. Authoritative DB verification for Project settings
        project_stmt = select(ProjectModel).where(ProjectModel.project_id == pid)
        project_model = self.session.execute(project_stmt).scalar_one_or_none()
        if not project_model or project_model.settings_hash != current_settings_hash:
            return None

        # 3. Lookup active matching approval
        stmt = (
            select(ApprovalModel)
            .where(
                ApprovalModel.project_id == pid,
                ApprovalModel.status == ApprovalStatus.APPROVED.value,
                ApprovalModel.is_approved.is_(True),
                ApprovalModel.script_hash == current_script_hash,
                ApprovalModel.settings_hash == current_settings_hash,
            )
            .order_by(ApprovalModel.approved_at.desc(), ApprovalModel.approval_id.desc())
            .limit(1)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def invalidate_for_project(self, project_id: UUID | str) -> int:
        """Revoke all active approvals for the project."""
        pid = _to_str_id(project_id)
        stmt = (
            update(ApprovalModel)
            .where(
                ApprovalModel.project_id == pid,
                ApprovalModel.status == ApprovalStatus.APPROVED.value,
            )
            .values(
                status=ApprovalStatus.INVALIDATED.value,
                is_approved=False,
            )
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return int(result.rowcount)


class GeneratedOutputRepository(BaseRepository):
    """Repository for managing generated skill outputs (prompts, thumbnail, SEO)."""

    def create(self, project_id: UUID | str, output: GeneratedOutput) -> GeneratedOutput:
        """Create a GeneratedOutput verifying project_id."""
        pid = _to_str_id(project_id)
        if str(output.project_id) != pid:
            raise ProjectMismatchError(
                f"GeneratedOutput project_id '{output.project_id}' does not match target project_id '{pid}'."
            )

        model = GeneratedOutputModel(
            output_id=str(output.output_id),
            project_id=pid,
            kind=output.kind.value,
            input_script_hash=output.input_script_hash,
            settings_hash=output.settings_hash,
            content_json=json.dumps(output.content, default=str),
            validation_report_json=json.dumps(output.validation_report.model_dump(), default=str),
            status=output.status.value,
            created_at=output.created_at,
        )
        try:
            self.session.add(model)
            self.session.flush()
        except IntegrityError as exc:
            raise ConstraintViolationError(f"Failed to create GeneratedOutput: {exc}") from exc
        return model.to_domain()

    def get_by_id(self, project_id: UUID | str, output_id: UUID | str) -> Optional[GeneratedOutput]:
        """Retrieve output by ID scoped by project_id."""
        pid = _to_str_id(project_id)
        oid = _to_str_id(output_id)
        stmt = select(GeneratedOutputModel).where(
            GeneratedOutputModel.output_id == oid,
            GeneratedOutputModel.project_id == pid,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def get_latest_by_kind(self, project_id: UUID | str, kind: OutputKind) -> Optional[GeneratedOutput]:
        """Retrieve newest valid output of a given kind for the project."""
        pid = _to_str_id(project_id)
        stmt = (
            select(GeneratedOutputModel)
            .where(
                GeneratedOutputModel.project_id == pid,
                GeneratedOutputModel.kind == kind.value,
                GeneratedOutputModel.status == OutputStatus.FRESH.value,
            )
            .order_by(GeneratedOutputModel.created_at.desc(), GeneratedOutputModel.output_id.desc())
            .limit(1)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None

    def list_by_project(self, project_id: UUID | str) -> list[GeneratedOutput]:
        """List all generated outputs for project ordered by created_at DESC."""
        pid = _to_str_id(project_id)
        stmt = (
            select(GeneratedOutputModel)
            .where(GeneratedOutputModel.project_id == pid)
            .order_by(GeneratedOutputModel.created_at.desc(), GeneratedOutputModel.output_id.desc())
        )
        models = self.session.execute(stmt).scalars().all()
        return [m.to_domain() for m in models]


class ExecutionEventRepository(BaseRepository):
    """Repository for managing DEC-018 metadata-only execution telemetry."""

    def create(self, project_id: UUID | str, event: ExecutionEvent) -> ExecutionEvent:
        """Create execution event enforcing DEC-018 allowlists and metadata-only boundaries."""
        pid = _to_str_id(project_id)
        if str(event.project_id) != pid:
            raise ProjectMismatchError(
                f"ExecutionEvent project_id '{event.project_id}' does not match target project_id '{pid}'."
            )

        # Allowlist enforcement
        error_category = getattr(event, "error_category", None)
        if error_category is not None and error_category not in ALLOWED_ERROR_CATEGORIES:
            raise ConstraintViolationError(
                f"Invalid error_category '{error_category}'. Must be one of {ALLOWED_ERROR_CATEGORIES}."
            )

        if event.error_code is not None and event.error_code not in ALLOWED_ERROR_CODES:
            raise ConstraintViolationError(
                f"Invalid error_code '{event.error_code}'. Must be one of {ALLOWED_ERROR_CODES}."
            )

        if event.fallback_reason is not None and event.fallback_reason not in ALLOWED_FALLBACK_REASONS:
            raise ConstraintViolationError(
                f"Invalid fallback_reason '{event.fallback_reason}'. Must be one of {ALLOWED_FALLBACK_REASONS}."
            )

        # Prohibited fields enforcement
        for field in PROHIBITED_EXECUTION_EVENT_FIELDS:
            if hasattr(event, field) and getattr(event, field):
                raise ConstraintViolationError(
                    f"DEC-018 Violation: Prohibited field '{field}' detected in ExecutionEvent."
                )

        tokens_in = event.token_usage.prompt_tokens if event.token_usage else None
        tokens_out = event.token_usage.completion_tokens if event.token_usage else None
        tokens_total = event.token_usage.total_tokens if event.token_usage else None

        model = ExecutionEventModel(
            event_id=str(event.event_id),
            project_id=pid,
            job_id=str(event.job_id),
            skill_id=event.skill_id.value,
            status=event.status.value,
            provider_id=event.provider_id,
            model_id=event.model_id,
            attempt_count=event.attempt_count,
            created_at=event.created_at,
            started_at=event.started_at,
            completed_at=event.completed_at,
            duration_ms=event.duration_ms,
            error_code=event.error_code,
            error_category=error_category,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            tokens_total=tokens_total,
            fallback_reason=event.fallback_reason,
            user_permission_granted=event.user_permission_granted,
        )
        try:
            self.session.add(model)
            self.session.flush()
        except IntegrityError as exc:
            raise ConstraintViolationError(f"Failed to create ExecutionEvent: {exc}") from exc
        return model.to_domain()

    def list_by_project(self, project_id: UUID | str, limit: int = 100) -> list[ExecutionEvent]:
        """List execution events ordered deterministically by created_at DESC, event_id DESC."""
        pid = _to_str_id(project_id)
        stmt = (
            select(ExecutionEventModel)
            .where(ExecutionEventModel.project_id == pid)
            .order_by(ExecutionEventModel.created_at.desc(), ExecutionEventModel.event_id.desc())
            .limit(limit)
        )
        models = self.session.execute(stmt).scalars().all()
        return [m.to_domain() for m in models]

    def count_by_project(self, project_id: UUID | str) -> int:
        """Count execution events for project."""
        pid = _to_str_id(project_id)
        stmt = (
            select(func.count())
            .select_from(ExecutionEventModel)
            .where(ExecutionEventModel.project_id == pid)
        )
        return int(self.session.execute(stmt).scalar_one())
