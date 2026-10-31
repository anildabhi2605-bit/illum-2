"""Domain package: Core domain entities, enums, value objects, and validators (P03-T01).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/ADR_001_TECHNOLOGY_STACK.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- DEC-018: Execution history retention & metadata policy (max 100 records FIFO)
- DEC-019: Active project limit reduction to 4
"""

from app.domain.constants import (
    APPROVED_VERTICAL_DURATIONS,
    LANDSCAPE_ASPECT_RATIO_STRING,
    LANDSCAPE_TARGET_HEIGHT,
    LANDSCAPE_TARGET_WIDTH,
    MAX_ACTIVE_PROJECTS,
    MAX_EXECUTION_HISTORY_PER_PROJECT,
    MAX_LANDSCAPE_PART_DURATION_SECONDS,
    MIN_LANDSCAPE_DURATION_SECONDS,
    MIN_LANDSCAPE_PART_DURATION_SECONDS,
    PROHIBITED_EXECUTION_EVENT_FIELDS,
    SEO_LANGUAGE,
    SUPPORTED_CONTENT_LANGUAGES,
    VERTICAL_ASPECT_RATIO_STRING,
    VERTICAL_DURATION_TO_PARTS_MAP,
    VERTICAL_PART_DURATION_SECONDS,
    VERTICAL_TARGET_HEIGHT,
    VERTICAL_TARGET_WIDTH,
)
from app.domain.enums import (
    AnalysisStatus,
    AnalysisType,
    ApprovalStatus,
    AspectRatio,
    ContentLanguage,
    JobStatus,
    OutputKind,
    OutputStatus,
    PartType,
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
from app.domain.validators import (
    validate_active_project_cap,
    validate_aspect_ratio_resolution,
    validate_execution_event_metadata_only,
    validate_hindi_devanagari,
    validate_landscape_duration,
    validate_script_parts,
    validate_script_structure,
    validate_seo_package,
    validate_vertical_duration,
)
from app.domain.value_objects import (
    ScriptPart,
    SEOPackage,
    TargetResolution,
    TokenUsage,
    ValidationReport,
)

__all__ = [
    # Constants
    "MAX_ACTIVE_PROJECTS",
    "MAX_EXECUTION_HISTORY_PER_PROJECT",
    "APPROVED_VERTICAL_DURATIONS",
    "VERTICAL_PART_DURATION_SECONDS",
    "VERTICAL_DURATION_TO_PARTS_MAP",
    "VERTICAL_TARGET_WIDTH",
    "VERTICAL_TARGET_HEIGHT",
    "VERTICAL_ASPECT_RATIO_STRING",
    "LANDSCAPE_TARGET_WIDTH",
    "LANDSCAPE_TARGET_HEIGHT",
    "LANDSCAPE_ASPECT_RATIO_STRING",
    "MIN_LANDSCAPE_DURATION_SECONDS",
    "MAX_LANDSCAPE_PART_DURATION_SECONDS",
    "MIN_LANDSCAPE_PART_DURATION_SECONDS",
    "SUPPORTED_CONTENT_LANGUAGES",
    "SEO_LANGUAGE",
    "PROHIBITED_EXECUTION_EVENT_FIELDS",
    # Enums
    "AspectRatio",
    "ContentLanguage",
    "ProjectStatus",
    "SourceType",
    "SourceStatus",
    "AnalysisType",
    "AnalysisStatus",
    "PartType",
    "ApprovalStatus",
    "OutputKind",
    "OutputStatus",
    "JobStatus",
    "SkillIdentifier",
    # Value Objects
    "TargetResolution",
    "ScriptPart",
    "ValidationReport",
    "TokenUsage",
    "SEOPackage",
    # Models
    "Project",
    "SourceVersion",
    "Analysis",
    "ScriptCurrent",
    "Approval",
    "GeneratedOutput",
    "ExecutionEvent",
    # Validators
    "validate_aspect_ratio_resolution",
    "validate_vertical_duration",
    "validate_landscape_duration",
    "validate_script_structure",
    "validate_script_parts",
    "validate_hindi_devanagari",
    "validate_seo_package",
    "validate_active_project_cap",
    "validate_execution_event_metadata_only",
]
