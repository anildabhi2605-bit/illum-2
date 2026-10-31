"""Validated value objects for ILLUM AI STUDIO domain layer (P03-T01).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/ADR_001_TECHNOLOGY_STACK.md
- 05_TESTING/ACCEPTANCE_MATRIX_PROPOSED.md (ACC-008, ACC-009A, ACC-012, ACC-016B, ACC-024A, ACC-024B, ACC-024C)
"""

from __future__ import annotations

import datetime
from typing import Optional

from app.domain.base import DomainBaseModel
from app.domain.enums import PartType


class TargetResolution(DomainBaseModel):
    """Width and height resolution pair."""
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Resolution dimensions must be positive, got {self.width}x{self.height}")


class ScriptPart(DomainBaseModel):
    """Single script scene part with duration, narration, and visual cue (ACC-016B).

    Invariants:
    - 9:16 Vertical part duration is strictly 8.0 seconds.
    - 16:9 Landscape part duration satisfies 0 < duration_seconds <= 8.0.
    """
    part_number: int
    part_type: PartType
    duration_seconds: float
    narration_text: str
    visual_cue: str
    audio_direction: Optional[str] = None

    def __init__(self, **data: object) -> None:
        super().__init__(**data)
        if self.part_number < 1:
            raise ValueError(f"part_number must be >= 1, got {self.part_number}")
        if self.duration_seconds <= 0.0:
            raise ValueError(f"Part duration must be strictly positive (> 0.0s), got {self.duration_seconds}s")
        if self.duration_seconds > 8.0:
            raise ValueError(f"Part duration cannot exceed 8.0s per invariant bounds, got {self.duration_seconds}s")
        if not self.narration_text or not self.narration_text.strip():
            raise ValueError("narration_text must not be empty")
        if not self.visual_cue or not self.visual_cue.strip():
            raise ValueError("visual_cue must not be empty")


class ValidationReport(DomainBaseModel):
    """Result of structural, linguistic, or schema validation."""
    is_valid: bool = True
    errors: list[str] = []
    warnings: list[str] = []
    validated_at: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)


class TokenUsage(DomainBaseModel):
    """Operational token usage metrics (ACC-030)."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __init__(self, **data: object) -> None:
        super().__init__(**data)
        if self.prompt_tokens < 0 or self.completion_tokens < 0 or self.total_tokens < 0:
            raise ValueError("Token counts cannot be negative")


class SEOPackage(DomainBaseModel):
    """Complete YouTube SEO package (ACC-024A, ACC-024B, ACC-024C).

    Invariants:
    - Language: 100% Roman Hindi using Latin alphabet.
    - Zero Devanagari Unicode characters (range U+0900 to U+097F).
    - Tags must be a clean comma-separated string without '#' or bullet numbers.
    - Zero fabricated search volumes or metrics.
    """
    title: str
    description: str
    hashtags: list[str]
    keywords: list[str]
    tags: str

    def __init__(self, **data: object) -> None:
        super().__init__(**data)
        # Check for Devanagari in any field (U+0900 to U+097F)
        for field_name in ("title", "description", "tags"):
            val = getattr(self, field_name, "")
            if any("\u0900" <= ch <= "\u097F" for ch in val):
                raise ValueError(
                    f"SEO field '{field_name}' contains Devanagari characters. "
                    "All SEO fields must be 100% Roman Hindi in Latin script."
                )

        for tag_str in self.hashtags:
            if any("\u0900" <= ch <= "\u097F" for ch in tag_str):
                raise ValueError("SEO hashtags must be Roman Hindi in Latin script (zero Devanagari characters).")

        for kw_str in self.keywords:
            if any("\u0900" <= ch <= "\u097F" for ch in kw_str):
                raise ValueError("SEO keywords must be Roman Hindi in Latin script (zero Devanagari characters).")

        # Validate tags string format (comma-separated, no # or bullets)
        if "#" in self.tags:
            raise ValueError("SEO tags string must be comma-separated values without '#' characters.")
        if any(line.strip().startswith(("-", "*", "1.", "2.")) for line in self.tags.split("\n")):
            raise ValueError("SEO tags string must not be formatted as a numbered or bulleted list.")
