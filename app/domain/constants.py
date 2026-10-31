"""Domain constants and invariants for ILLUM AI STUDIO (P03-T01).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/ADR_001_TECHNOLOGY_STACK.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- DEC-018: Execution history retention & metadata policy (max 100 records FIFO, metadata only)
- DEC-019: Active project limit reduction to 4
"""

from typing import Final

# DEC-019: Maximum active saved projects
MAX_ACTIVE_PROJECTS: Final[int] = 4

# DEC-018: Maximum execution history records per project
MAX_EXECUTION_HISTORY_PER_PROJECT: Final[int] = 100

# Vertical (9:16) invariants (ACC-008, ACC-009, ACC-009A, ACC-010)
VERTICAL_ASPECT_RATIO_STRING: Final[str] = "9:16"
VERTICAL_TARGET_WIDTH: Final[int] = 1080
VERTICAL_TARGET_HEIGHT: Final[int] = 1920
APPROVED_VERTICAL_DURATIONS: Final[tuple[int, ...]] = (24, 32, 40, 48, 56)
VERTICAL_PART_DURATION_SECONDS: Final[float] = 8.0
VERTICAL_DURATION_TO_PARTS_MAP: Final[dict[int, int]] = {
    24: 3,
    32: 4,
    40: 5,
    48: 6,
    56: 7,
}

# Landscape (16:9) invariants (ACC-008, ACC-011, ACC-012, ACC-012A)
LANDSCAPE_ASPECT_RATIO_STRING: Final[str] = "16:9"
LANDSCAPE_TARGET_WIDTH: Final[int] = 1920
LANDSCAPE_TARGET_HEIGHT: Final[int] = 1080
MIN_LANDSCAPE_DURATION_SECONDS: Final[float] = 180.0
MAX_LANDSCAPE_PART_DURATION_SECONDS: Final[float] = 8.0
MIN_LANDSCAPE_PART_DURATION_SECONDS: Final[float] = 0.0  # strictly > 0.0

# Supported languages (01_BASELINE Section 3)
SUPPORTED_CONTENT_LANGUAGES: Final[tuple[str, ...]] = ("en", "hi")
SEO_LANGUAGE: Final[str] = "Roman Hindi"  # Latin script only

# Prohibited execution event fields (DEC-018 negative invariant)
PROHIBITED_EXECUTION_EVENT_FIELDS: Final[frozenset[str]] = frozenset({
    "prompt",
    "raw_prompt",
    "prompts",
    "raw_prompts",
    "source_text",
    "raw_source",
    "source_content",
    "raw_content",
    "request_body",
    "raw_request",
    "raw_llm_request",
    "response_body",
    "raw_response",
    "raw_llm_response",
    "payload",
    "raw_payload",
    "api_key",
    "secret",
})
