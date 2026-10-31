"""Unit and security tests for project-scoped repositories (P03-T03).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- DEC-018: Metadata-only execution events, allowlists, deterministic ordering
- DEC-019: Project scoping, isolation, active counting, oldest retrieval, cascade deletion
- ACC-018: Single active script savepoint failure atomicity
"""

from __future__ import annotations

import datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.enums import (
    AnalysisType,
    ApprovalStatus,
    AspectRatio,
    ContentLanguage,
    JobStatus,
    OutputKind,
    PartType,
    SkillIdentifier,
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
from app.persistence.database import set_connection_pragmas
from app.persistence.exceptions import (
    ConstraintViolationError,
    ProjectMismatchError,
)
from app.persistence.models import (
    ApprovalModel,
    Base,
)
from app.persistence.repositories import (
    AnalysisRepository,
    ApprovalRepository,
    CurrentScriptRepository,
    ExecutionEventRepository,
    GeneratedOutputRepository,
    ProjectRepository,
    SourceVersionRepository,
)


@pytest.fixture
def db_session(tmp_path: Path):
    """Provide a fresh SQLite session backed by a temporary file with WAL and pragmas."""
    db_file = tmp_path / "test_repo.db"
    engine = create_engine(f"sqlite:///{db_file}")

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, record):
        set_connection_pragmas(dbapi_conn)

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _create_sample_project(session: Session, title: str = "Test Project") -> Project:
    repo = ProjectRepository(session)
    project = Project(
        project_id=uuid4(),
        title=title,
        aspect_ratio=AspectRatio.VERTICAL_9_16,
        target_resolution=TargetResolution(width=1080, height=1920),
        duration_seconds=32.0,
        part_count=4,
        content_language=ContentLanguage.ENGLISH,
        settings_hash="settings_hash_v1",
    )
    saved = repo.create(project)
    session.commit()
    return saved


def _create_sample_script(project_id: UUID, content_hash: str = "script_hash_v1") -> ScriptCurrent:
    parts = [
        ScriptPart(
            part_number=1,
            part_type=PartType.HOOK,
            narration_text="Narration 1",
            visual_cue="Visual 1",
            duration_seconds=8.0,
        )
    ]
    report = ValidationReport(is_valid=True)
    return ScriptCurrent(
        project_id=project_id,
        title="Active Script",
        parts=parts,
        content_hash=content_hash,
        source_version_used=1,
        settings_hash="settings_hash_v1",
        validation_report=report,
    )


# ---------------------------------------------------------------------------
# 1. ProjectRepository CRUD, Isolation, Count & Oldest
# ---------------------------------------------------------------------------

def test_project_repository_crud(db_session: Session):
    repo = ProjectRepository(db_session)
    p = _create_sample_project(db_session, "Project Alpha")

    fetched = repo.get_by_id(p.project_id)
    assert fetched is not None
    assert fetched.title == "Project Alpha"

    p.title = "Project Alpha Renamed"
    updated = repo.update(p)
    db_session.commit()
    assert updated.title == "Project Alpha Renamed"

    active_list = repo.list_active()
    assert len(active_list) == 1
    assert active_list[0].project_id == p.project_id


def test_project_count_and_oldest_active(db_session: Session):
    repo = ProjectRepository(db_session)
    base_time = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)

    for i in range(4):
        p = Project(
            project_id=uuid4(),
            title=f"Project {i}",
            aspect_ratio=AspectRatio.VERTICAL_9_16,
            target_resolution=TargetResolution(width=1080, height=1920),
            duration_seconds=32.0,
            part_count=4,
            created_at=base_time + datetime.timedelta(days=i),
        )
        repo.create(p)
    db_session.commit()

    assert repo.count_active() == 4
    oldest = repo.get_oldest_active()
    assert oldest is not None
    assert oldest.title == "Project 0"


def test_project_cascading_deletion(db_session: Session):
    p = _create_sample_project(db_session, "Parent Project")
    source_repo = SourceVersionRepository(db_session)
    script_repo = CurrentScriptRepository(db_session)

    source = SourceVersion(
        project_id=p.project_id,
        title="Source 1",
        source_type=SourceType.PASTED,
        saved_content="Content",
        content_hash="hash1",
    )
    source_repo.create(p.project_id, source)
    script = _create_sample_script(p.project_id)
    script_repo.save_or_replace(p.project_id, script)
    db_session.commit()

    assert source_repo.get_latest(p.project_id) is not None
    assert script_repo.get(p.project_id) is not None

    proj_repo = ProjectRepository(db_session)
    deleted = proj_repo.delete(p.project_id)
    db_session.commit()
    assert deleted is True

    assert source_repo.get_latest(p.project_id) is None
    assert script_repo.get(p.project_id) is None


# ---------------------------------------------------------------------------
# 2. Explicit Project Scoping on Create Rejects Mismatches
# ---------------------------------------------------------------------------

def test_create_methods_reject_project_mismatches(db_session: Session):
    p1 = _create_sample_project(db_session, "Proj 1")
    p2 = _create_sample_project(db_session, "Proj 2")

    source = SourceVersion(
        project_id=p1.project_id,
        title="Source",
        source_type=SourceType.PASTED,
        saved_content="Data",
        content_hash="h1",
    )
    with pytest.raises(ProjectMismatchError):
        SourceVersionRepository(db_session).create(p2.project_id, source)

    analysis = Analysis(
        project_id=p1.project_id,
        analysis_type=AnalysisType.SOURCE,
        input_hash="h1",
        output_payload={"key": "val"},
    )
    with pytest.raises(ProjectMismatchError):
        AnalysisRepository(db_session).create(p2.project_id, analysis)

    script = _create_sample_script(p1.project_id)
    with pytest.raises(ProjectMismatchError):
        CurrentScriptRepository(db_session).save_or_replace(p2.project_id, script)

    approval = Approval(
        project_id=p1.project_id,
        script_hash="h1",
        settings_hash="s1",
    )
    with pytest.raises(ProjectMismatchError):
        ApprovalRepository(db_session).create(p2.project_id, approval)

    output = GeneratedOutput(
        project_id=p1.project_id,
        kind=OutputKind.SEO_PACKAGE,
        input_script_hash="h1",
        settings_hash="s1",
        content={"tags": []},
        validation_report=ValidationReport(is_valid=True),
    )
    with pytest.raises(ProjectMismatchError):
        GeneratedOutputRepository(db_session).create(p2.project_id, output)

    event = ExecutionEvent(
        project_id=p1.project_id,
        skill_id=SkillIdentifier.SKILL_A,
        status=JobStatus.COMPLETED,
        provider_id="groq",
        model_id="llama3",
    )
    with pytest.raises(ProjectMismatchError):
        ExecutionEventRepository(db_session).create(p2.project_id, event)


# ---------------------------------------------------------------------------
# 3. Cross-Project Isolation Negative Tests
# ---------------------------------------------------------------------------

def test_cross_project_isolation_reads(db_session: Session):
    p1 = _create_sample_project(db_session, "Proj 1")
    p2 = _create_sample_project(db_session, "Proj 2")

    source_repo = SourceVersionRepository(db_session)
    source = SourceVersion(
        project_id=p1.project_id,
        title="Source",
        source_type=SourceType.PASTED,
        saved_content="Data",
        content_hash="h1",
    )
    saved_source = source_repo.create(p1.project_id, source)
    db_session.commit()

    # Accessing P1's source with P2's project_id returns None
    assert source_repo.get_by_id(p2.project_id, saved_source.source_id) is None
    assert source_repo.list_by_project(p2.project_id) == []


# ---------------------------------------------------------------------------
# 4. CurrentScript Savepoint Failure Atomicity (ACC-018)
# ---------------------------------------------------------------------------

def test_current_script_savepoint_failure_atomicity(db_session: Session):
    p = _create_sample_project(db_session, "Script Test Project")
    repo = CurrentScriptRepository(db_session)

    # 1. Save valid initial script
    script_v1 = _create_sample_script(p.project_id, "hash_v1")
    repo.save_or_replace(p.project_id, script_v1)
    db_session.commit()

    initial = repo.get(p.project_id)
    assert initial is not None
    assert initial.content_hash == "hash_v1"

    # 2. Attempt replacement that fails inside nested transaction (simulate flush failure)
    candidate_script = _create_sample_script(p.project_id, "hash_candidate")
    
    real_flush = repo.session.flush
    def broken_flush():
        raise RuntimeError("Simulated nested flush failure!")

    repo.session.flush = broken_flush  # type: ignore
    try:
        with pytest.raises(RuntimeError):
            repo.save_or_replace(p.project_id, candidate_script)
    finally:
        repo.session.flush = real_flush

    # Caller catches exception and attempts commit
    db_session.commit()

    # Original script must remain completely intact in DB
    rechecked = repo.get(p.project_id)
    assert rechecked is not None
    assert rechecked.content_hash == "hash_v1"


# ---------------------------------------------------------------------------
# 5. Approval Lifecycle, No Silent Promotion & Authoritative Hash Verification
# ---------------------------------------------------------------------------

def test_approval_no_silent_promotion(db_session: Session):
    p = _create_sample_project(db_session)
    repo = ApprovalRepository(db_session)

    # Persisting a draft approval must NOT silently promote to approved
    draft = Approval(
        project_id=p.project_id,
        script_hash="script_hash_v1",
        settings_hash="settings_hash_v1",
        status=ApprovalStatus.DRAFT,
        is_approved=False,
    )
    saved = repo.create(p.project_id, draft)
    db_session.commit()

    assert saved.status == ApprovalStatus.DRAFT
    assert saved.is_approved is False

    # Direct query in DB
    model = db_session.execute(
        select(ApprovalModel).where(ApprovalModel.approval_id == str(saved.approval_id))
    ).scalar_one()
    assert model.status == "draft"
    assert model.is_approved is False


def test_approval_authoritative_hash_verification(db_session: Session):
    p = _create_sample_project(db_session)
    script_repo = CurrentScriptRepository(db_session)
    approval_repo = ApprovalRepository(db_session)

    script = _create_sample_script(p.project_id, "script_hash_v1")
    script_repo.save_or_replace(p.project_id, script)

    # Create explicit approved record
    approved = Approval(
        project_id=p.project_id,
        script_hash="script_hash_v1",
        settings_hash="settings_hash_v1",
        status=ApprovalStatus.APPROVED,
        is_approved=True,
        approved_at=datetime.datetime.now(datetime.timezone.utc),
    )
    approval_repo.create(p.project_id, approved)
    db_session.commit()

    # Valid query matching DB authoritative hashes
    current = approval_repo.get_current(p.project_id, "script_hash_v1", "settings_hash_v1")
    assert current is not None
    assert current.is_approved is True

    # Stale caller-supplied script hash returns None
    assert approval_repo.get_current(p.project_id, "stale_script_hash", "settings_hash_v1") is None

    # Stale caller-supplied settings hash returns None
    assert approval_repo.get_current(p.project_id, "script_hash_v1", "stale_settings_hash") is None

    # Invalidate approvals
    invalidated_count = approval_repo.invalidate_for_project(p.project_id)
    db_session.commit()
    assert invalidated_count == 1

    # Revoked approval is never returned as current
    assert approval_repo.get_current(p.project_id, "script_hash_v1", "settings_hash_v1") is None


# ---------------------------------------------------------------------------
# 6. ExecutionEvent Ordering & DEC-018 Allowlist Enforcement
# ---------------------------------------------------------------------------

def test_execution_event_ordering_and_allowlists(db_session: Session):
    p = _create_sample_project(db_session)
    repo = ExecutionEventRepository(db_session)

    base_time = datetime.datetime(2026, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    for i in range(3):
        event = ExecutionEvent(
            project_id=p.project_id,
            skill_id=SkillIdentifier.SKILL_A,
            status=JobStatus.COMPLETED,
            provider_id="groq",
            model_id="llama3",
            created_at=base_time + datetime.timedelta(minutes=i),
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )
        repo.create(p.project_id, event)
    db_session.commit()

    events = repo.list_by_project(p.project_id)
    assert len(events) == 3
    # Ordered created_at DESC
    assert events[0].created_at > events[1].created_at > events[2].created_at


def test_execution_event_allowlist_violations(db_session: Session):
    p = _create_sample_project(db_session)
    repo = ExecutionEventRepository(db_session)

    # Invalid error category
    event_bad_cat = ExecutionEvent(
        project_id=p.project_id,
        skill_id=SkillIdentifier.SKILL_A,
        status=JobStatus.FAILED,
        provider_id="groq",
        model_id="llama3",
        error_category="INVALID_CAT",
    )
    with pytest.raises(ConstraintViolationError):
        repo.create(p.project_id, event_bad_cat)

    # Invalid error code
    event_bad_code = ExecutionEvent(
        project_id=p.project_id,
        skill_id=SkillIdentifier.SKILL_A,
        status=JobStatus.FAILED,
        provider_id="groq",
        model_id="llama3",
        error_code="RAW_ERR_500",
    )
    with pytest.raises(ConstraintViolationError):
        repo.create(p.project_id, event_bad_code)

    # Invalid fallback reason
    event_bad_fb = ExecutionEvent(
        project_id=p.project_id,
        skill_id=SkillIdentifier.SKILL_A,
        status=JobStatus.FAILED,
        provider_id="groq",
        model_id="llama3",
        fallback_reason="Raw timeout string",
    )
    with pytest.raises(ConstraintViolationError):
        repo.create(p.project_id, event_bad_fb)


# ---------------------------------------------------------------------------
# 7. Shared .env File Preservation on Project Deletion
# ---------------------------------------------------------------------------

def test_shared_env_file_preservation(db_session: Session, tmp_path: Path):
    p = _create_sample_project(db_session, "Env Protection Project")
    repo = ProjectRepository(db_session)

    env_path = Path(".env")
    env_existed_before = env_path.exists()
    original_content = env_path.read_text(encoding="utf-8") if env_existed_before else None

    try:
        if not env_existed_before:
            env_path.write_text("DUMMY_KEY=test_secret\n", encoding="utf-8")

        # Delete project
        repo.delete(p.project_id)
        db_session.commit()

        # .env must still exist with intact content
        assert env_path.exists()
        if original_content is not None:
            assert env_path.read_text(encoding="utf-8") == original_content
        else:
            assert env_path.read_text(encoding="utf-8") == "DUMMY_KEY=test_secret\n"
    finally:
        if not env_existed_before and env_path.exists():
            env_path.unlink()
