"""Centralized domain validators for ILLUM AI STUDIO (P03-T01).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/ADR_001_TECHNOLOGY_STACK.md (Section 3.4)
- 05_TESTING/ACCEPTANCE_MATRIX_PROPOSED.md
  (ACC-008, ACC-009, ACC-009A, ACC-010, ACC-011, ACC-012, ACC-012A, ACC-016B, ACC-024A, ACC-024B, ACC-024C)
- DEC-018: Execution history retention & metadata policy
- DEC-019: Active project limit reduction to 4
"""

from __future__ import annotations

import math
from typing import Any, Optional

from app.domain.constants import (
    APPROVED_VERTICAL_DURATIONS,
    LANDSCAPE_TARGET_HEIGHT,
    LANDSCAPE_TARGET_WIDTH,
    MAX_ACTIVE_PROJECTS,
    MAX_LANDSCAPE_PART_DURATION_SECONDS,
    MIN_LANDSCAPE_DURATION_SECONDS,
    MIN_LANDSCAPE_PART_DURATION_SECONDS,
    PROHIBITED_EXECUTION_EVENT_FIELDS,
    VERTICAL_DURATION_TO_PARTS_MAP,
    VERTICAL_PART_DURATION_SECONDS,
    VERTICAL_TARGET_HEIGHT,
    VERTICAL_TARGET_WIDTH,
)
from app.domain.enums import AspectRatio, PartType
from app.domain.value_objects import ScriptPart, SEOPackage, TargetResolution


def validate_aspect_ratio_resolution(
    aspect_ratio: AspectRatio,
    resolution: TargetResolution,
) -> None:
    """Validate target resolution matches approved aspect ratio (ACC-008).

    - 9:16 Vertical: target resolution strictly 1080x1920.
    - 16:9 Landscape: target resolution strictly 1920x1080.
    """
    if aspect_ratio == AspectRatio.VERTICAL_9_16:
        if resolution.width != VERTICAL_TARGET_WIDTH or resolution.height != VERTICAL_TARGET_HEIGHT:
            raise ValueError(
                f"Invalid resolution for 9:16 Vertical. Expected {VERTICAL_TARGET_WIDTH}x{VERTICAL_TARGET_HEIGHT}, "
                f"got {resolution.width}x{resolution.height}."
            )
    elif aspect_ratio == AspectRatio.LANDSCAPE_16_9:
        if resolution.width != LANDSCAPE_TARGET_WIDTH or resolution.height != LANDSCAPE_TARGET_HEIGHT:
            raise ValueError(
                f"Invalid resolution for 16:9 Landscape. Expected {LANDSCAPE_TARGET_WIDTH}x{LANDSCAPE_TARGET_HEIGHT}, "
                f"got {resolution.width}x{resolution.height}."
            )
    else:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")


def validate_vertical_duration(
    total_duration: float,
    parts: Optional[list[ScriptPart]] = None,
) -> None:
    """Validate Vertical 9:16 duration and part constraints (ACC-009, ACC-009A, ACC-010, ACC-016B).

    Invariants:
    1. Total duration T in {24, 32, 40, 48, 56} seconds. 60s or any other duration is strictly rejected.
    2. Part count N = T / 8 in {3, 4, 5, 6, 7}.
    3. Every part duration d_i == 8.0 seconds.
    4. Sum of parts == total_duration.
    5. Structure: Part 1 is Hook, Parts 2..N-1 are Story, Part N is Ending.
    """
    int_duration = int(round(total_duration))
    if not math.isclose(total_duration, float(int_duration), abs_tol=1e-3) or int_duration not in APPROVED_VERTICAL_DURATIONS:
        raise ValueError(
            f"Unsupported vertical duration {total_duration}s. Approved 9:16 vertical durations "
            f"are strictly 24, 32, 40, 48, or 56 seconds (ACC-009, ACC-010). "
            f"60 seconds or other values are not approved."
        )

    expected_parts = VERTICAL_DURATION_TO_PARTS_MAP[int_duration]

    if parts is not None:
        if len(parts) != expected_parts:
            raise ValueError(
                f"Vertical 9:16 duration {int_duration}s requires exactly {expected_parts} parts "
                f"(T / 8), but got {len(parts)} parts (ACC-009A)."
            )

        duration_sum = 0.0
        for i, part in enumerate(parts):
            if not math.isclose(part.duration_seconds, VERTICAL_PART_DURATION_SECONDS, abs_tol=1e-3):
                raise ValueError(
                    f"Part {part.part_number} duration is {part.duration_seconds}s. "
                    f"Every vertical 9:16 part must be exactly {VERTICAL_PART_DURATION_SECONDS}s (ACC-009A)."
                )
            duration_sum += part.duration_seconds

        if not math.isclose(duration_sum, float(int_duration), abs_tol=1e-3):
            raise ValueError(
                f"Sum of vertical part durations ({duration_sum}s) does not equal total duration ({int_duration}s)."
            )

        # Structure validation (ACC-016B)
        validate_script_structure(parts)


def validate_landscape_duration(
    total_duration: float,
    parts: Optional[list[ScriptPart]] = None,
) -> None:
    """Validate Landscape 16:9 duration and part constraints (ACC-011, ACC-012, ACC-012A, ACC-016B).

    Invariants:
    1. Total duration T >= 180.0 seconds.
    2. Every part duration satisfies 0 < d_i <= 8.0 seconds.
    3. Sum of parts == total_duration.
    4. Structure: Part 1 is Hook, Parts 2..N-1 are Story, Part N is Ending.
    """
    if total_duration < MIN_LANDSCAPE_DURATION_SECONDS:
        raise ValueError(
            f"Landscape 16:9 total duration {total_duration}s is less than the required minimum "
            f"of {MIN_LANDSCAPE_DURATION_SECONDS}s (ACC-011)."
        )

    if parts is not None:
        if not parts:
            raise ValueError("Landscape script parts list cannot be empty.")

        duration_sum = 0.0
        for part in parts:
            if part.duration_seconds <= MIN_LANDSCAPE_PART_DURATION_SECONDS or part.duration_seconds > MAX_LANDSCAPE_PART_DURATION_SECONDS:
                raise ValueError(
                    f"Part {part.part_number} duration {part.duration_seconds}s violates landscape bound: "
                    f"must satisfy 0.0 < d_i <= {MAX_LANDSCAPE_PART_DURATION_SECONDS}s (ACC-012)."
                )
            duration_sum += part.duration_seconds

        if not math.isclose(duration_sum, total_duration, abs_tol=1e-3):
            raise ValueError(
                f"Sum of landscape part durations ({duration_sum}s) does not match total duration "
                f"({total_duration}s) (ACC-012A)."
            )

        # Structure validation (ACC-016B)
        validate_script_structure(parts)


def validate_script_structure(parts: list[ScriptPart]) -> None:
    """Validate Hook -> Story -> Ending part sequence (ACC-016B).

    - Part 1 must be Hook.
    - Parts 2 to N-1 must be Story.
    - Part N must be Ending.
    """
    n = len(parts)
    if n < 3:
        raise ValueError(f"Script must have at least 3 parts for Hook-Story-Ending structure, got {n}.")

    for idx, part in enumerate(parts):
        expected_num = idx + 1
        if part.part_number != expected_num:
            raise ValueError(f"Part at index {idx} has part_number {part.part_number}; expected {expected_num}.")

        if idx == 0:
            if part.part_type != PartType.HOOK:
                raise ValueError(f"Part 1 must be of type HOOK, got {part.part_type.value} (ACC-016B).")
        elif idx == n - 1:
            if part.part_type != PartType.ENDING:
                raise ValueError(f"Final part ({n}) must be of type ENDING, got {part.part_type.value} (ACC-016B).")
        else:
            if part.part_type != PartType.STORY:
                raise ValueError(
                    f"Intermediate part {expected_num} must be of type STORY, got {part.part_type.value} (ACC-016B)."
                )


def validate_script_parts(
    aspect_ratio: AspectRatio,
    total_duration: float,
    parts: list[ScriptPart],
) -> None:
    """Dispatch script part validation according to aspect ratio."""
    if aspect_ratio == AspectRatio.VERTICAL_9_16:
        validate_vertical_duration(total_duration, parts)
    elif aspect_ratio == AspectRatio.LANDSCAPE_16_9:
        validate_landscape_duration(total_duration, parts)
    else:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")


def validate_hindi_devanagari(text: str) -> bool:
    """Check if text contains Devanagari script characters (U+0900 to U+097F)."""
    return any("\u0900" <= ch <= "\u097F" for ch in text)


def validate_seo_package(seo: SEOPackage) -> None:
    """Validate YouTube SEO package invariants (ACC-024A, ACC-024B, ACC-024C).

    - All 5 fields must be 100% Roman Hindi in Latin alphabet (zero Devanagari).
    - Tags must be a clean comma-separated string without '#' or list bullets.
    - Zero fabricated search volumes or rankings.
    """
    # Prohibit fake metrics keywords
    fake_metrics_terms = [
        "monthly search",
        "search volume",
        "monthly searches",
        "cpc",
        "ranking guarantee",
        "guaranteed views",
    ]
    combined_seo_text = f"{seo.title} {seo.description} {seo.tags} {' '.join(seo.keywords)}".lower()
    for term in fake_metrics_terms:
        if term in combined_seo_text:
            raise ValueError(
                f"SEO output contains prohibited fabricated metric '{term}' (ACC-024C)."
            )


def validate_active_project_cap(active_count: int) -> None:
    """Enforce maximum 4 active saved projects per DEC-019 (ACC-005, ACC-006)."""
    if active_count > MAX_ACTIVE_PROJECTS:
        raise ValueError(
            f"Active project limit exceeded: maximum allowed is {MAX_ACTIVE_PROJECTS}, got {active_count} (DEC-019)."
        )


def validate_execution_event_metadata_only(event_dict: dict[str, Any]) -> None:
    """Assert execution history payload contains metadata only per DEC-018 (ACC-030B)."""
    prohibited = PROHIBITED_EXECUTION_EVENT_FIELDS.intersection(event_dict.keys())
    if prohibited:
        raise ValueError(
            f"DEC-018 Security Invariant Violation: Execution event contains prohibited raw payload fields: {sorted(prohibited)}"
        )
