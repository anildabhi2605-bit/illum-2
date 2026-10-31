"""State enums and domain types for ILLUM AI STUDIO (P03-T01).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
"""

from enum import Enum


class AspectRatio(str, Enum):
    """Aspect ratio choices per ADR-001 and Baseline Rules (ACC-008)."""
    VERTICAL_9_16 = "9:16"
    LANDSCAPE_16_9 = "16:9"


class ContentLanguage(str, Enum):
    """Project and narration language choices (Baseline Section 3)."""
    ENGLISH = "en"
    HINDI = "hi"


class ProjectStatus(str, Enum):
    """Lifecycle status of a project."""
    ACTIVE = "active"
    ARCHIVED = "archived"


class SourceType(str, Enum):
    """Origin type of source material."""
    PASTED = "pasted"
    URL = "url"
    IMPORTED = "imported"


class SourceStatus(str, Enum):
    """Validation status of source material (ACC-013, ACC-014)."""
    UNVALIDATED = "unvalidated"
    VALIDATED = "validated"
    STALE = "stale"


class AnalysisType(str, Enum):
    """Type of cached analysis."""
    SOURCE = "source"
    SCRIPT = "script"


class AnalysisStatus(str, Enum):
    """Validity state of an analysis."""
    VALID = "valid"
    STALE = "stale"


class PartType(str, Enum):
    """Structural role of a script part (ACC-016B)."""
    HOOK = "hook"
    STORY = "story"
    ENDING = "ending"


class ApprovalStatus(str, Enum):
    """Script approval gate status (ACC-019, ACC-020)."""
    DRAFT = "draft"
    APPROVED = "approved"
    INVALIDATED = "invalidated"


class OutputKind(str, Enum):
    """Classification of generated downstream outputs."""
    VIDEO_PROMPT = "video_prompt"
    THUMBNAIL_PROMPT = "thumbnail_prompt"
    SEO_PACKAGE = "seo_package"
    RESEARCH_DOSSIER = "research_dossier"


class OutputStatus(str, Enum):
    """Freshness status of generated outputs (ACC-015, ACC-022)."""
    FRESH = "fresh"
    STALE = "stale"


class JobStatus(str, Enum):
    """Execution state of a job (ACC-028, ACC-029)."""
    QUEUED = "queued"
    RUNNING = "running"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SkillIdentifier(str, Enum):
    """Four protected skills + Module E."""
    SKILL_A = "skill_a"  # Story to Script
    SKILL_B = "skill_b"  # Script to Video Prompts
    SKILL_C = "skill_c"  # Thumbnail Intelligence
    SKILL_D = "skill_d"  # YouTube SEO
    MODULE_E = "module_e"  # Idea Research
