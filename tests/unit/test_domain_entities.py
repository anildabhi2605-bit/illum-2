"""Unit tests for ILLUM AI STUDIO domain models, value objects, and invariants (P03-T01).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/ADR_001_TECHNOLOGY_STACK.md
- 05_TESTING/ACCEPTANCE_MATRIX_PROPOSED.md
  (ACC-004, ACC-008, ACC-009, ACC-009A, ACC-010, ACC-011, ACC-012, ACC-012A, ACC-016B, ACC-018, ACC-024A, ACC-024B, ACC-024C, ACC-030A, ACC-030B)
- DEC-018: Execution history retention & metadata policy
- DEC-019: Active project limit reduction to 4
"""

import datetime
import unittest
from uuid import uuid4

from app.domain.constants import (
    APPROVED_VERTICAL_DURATIONS,
    MAX_ACTIVE_PROJECTS,
    MAX_EXECUTION_HISTORY_PER_PROJECT,
    VERTICAL_DURATION_TO_PARTS_MAP,
)
from app.domain.enums import (
    ApprovalStatus,
    AspectRatio,
    ContentLanguage,
    JobStatus,
    OutputKind,
    PartType,
    ProjectStatus,
    SkillIdentifier,
    SourceStatus,
    SourceType,
)
from app.domain.models import (
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
    validate_landscape_duration,
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


class TestVerticalDurations(unittest.TestCase):
    """Test 9:16 Vertical duration rules per ACC-009, ACC-009A, ACC-010, ACC-016B."""

    def _build_parts(self, count: int, part_duration: float = 8.0) -> list[ScriptPart]:
        parts = []
        for i in range(1, count + 1):
            if i == 1:
                pt = PartType.HOOK
            elif i == count:
                pt = PartType.ENDING
            else:
                pt = PartType.STORY
            parts.append(
                ScriptPart(
                    part_number=i,
                    part_type=pt,
                    duration_seconds=part_duration,
                    narration_text=f"Scene {i} narration.",
                    visual_cue=f"Visual cue {i}.",
                )
            )
        return parts

    def test_approved_vertical_durations_succeed(self):
        """ACC-009: Test T in {24, 32, 40, 48, 56} with parts N in {3, 4, 5, 6, 7} and d_i == 8.0s."""
        for duration in APPROVED_VERTICAL_DURATIONS:
            expected_parts = VERTICAL_DURATION_TO_PARTS_MAP[duration]
            parts = self._build_parts(expected_parts, part_duration=8.0)

            # Assert validation succeeds without error
            validate_vertical_duration(float(duration), parts)
            self.assertEqual(len(parts), expected_parts)
            self.assertEqual(sum(p.duration_seconds for p in parts), float(duration))

    def test_unapproved_vertical_duration_rejected(self):
        """ACC-010: Reject 60 seconds and any unsupported duration (e.g. 20, 30, 45, 60, 64)."""
        unsupported = [20.0, 30.0, 45.0, 60.0, 64.0, 90.0]
        for bad_dur in unsupported:
            with self.subTest(duration=bad_dur):
                with self.assertRaises(ValueError) as ctx:
                    validate_vertical_duration(bad_dur)
                self.assertIn("Unsupported vertical duration", str(ctx.exception))
                self.assertIn("60 seconds", str(ctx.exception))

    def test_non_8s_part_duration_rejected(self):
        """ACC-009A: Reject any vertical part duration d_i != 8.0s."""
        parts = self._build_parts(3, part_duration=8.0)
        # Tamper part 2 to 7.5s (sum becomes 23.5s)
        parts[1] = ScriptPart(
            part_number=2,
            part_type=PartType.STORY,
            duration_seconds=7.5,
            narration_text="Tampered narration",
            visual_cue="Tampered cue",
        )
        with self.assertRaises(ValueError) as ctx:
            validate_vertical_duration(24.0, parts)
        self.assertIn("must be exactly 8.0s", str(ctx.exception))

    def test_mismatched_part_count_rejected(self):
        """Reject part count != T / 8 for vertical 9:16."""
        # 24s requires 3 parts; pass 4 parts of 6s or 4 parts of 8s
        parts = self._build_parts(4, part_duration=8.0)
        with self.assertRaises(ValueError) as ctx:
            validate_vertical_duration(24.0, parts)
        self.assertIn("requires exactly 3 parts", str(ctx.exception))

    def test_invalid_structure_rejected(self):
        """ACC-016B: Part 1 must be HOOK, Part N must be ENDING, intermediate STORY."""
        parts = [
            ScriptPart(part_number=1, part_type=PartType.STORY, duration_seconds=8.0, narration_text="N1", visual_cue="V1"),
            ScriptPart(part_number=2, part_type=PartType.STORY, duration_seconds=8.0, narration_text="N2", visual_cue="V2"),
            ScriptPart(part_number=3, part_type=PartType.ENDING, duration_seconds=8.0, narration_text="N3", visual_cue="V3"),
        ]
        with self.assertRaises(ValueError) as ctx:
            validate_script_structure(parts)
        self.assertIn("Part 1 must be of type HOOK", str(ctx.exception))


class TestLandscapeDurations(unittest.TestCase):
    """Test 16:9 Landscape duration rules per ACC-011, ACC-012, ACC-012A, ACC-016B."""

    def _build_landscape_parts(self, total_seconds: float) -> list[ScriptPart]:
        # 180s minimum -> 23 parts (22 parts of 8s = 176s + 1 part of 4s = 180s)
        parts = []
        remaining = total_seconds
        part_idx = 1
        while remaining > 0.0:
            dur = min(8.0, remaining)
            dur = round(dur, 2)
            parts.append(
                ScriptPart(
                    part_number=part_idx,
                    part_type=PartType.HOOK if part_idx == 1 else PartType.STORY,
                    duration_seconds=dur,
                    narration_text=f"Landscape scene {part_idx}.",
                    visual_cue=f"Landscape cue {part_idx}.",
                )
            )
            remaining -= dur
            part_idx += 1

        parts[-1].part_type = PartType.ENDING
        return parts

    def test_landscape_valid_duration_succeeds(self):
        """ACC-011, ACC-012, ACC-012A: 180s landscape script passes validation."""
        parts = self._build_landscape_parts(180.0)
        validate_landscape_duration(180.0, parts)
        self.assertGreaterEqual(len(parts), 23)
        self.assertAlmostEqual(sum(p.duration_seconds for p in parts), 180.0, places=2)

    def test_landscape_duration_under_180s_rejected(self):
        """ACC-011: Total duration < 180.0s is rejected."""
        with self.assertRaises(ValueError) as ctx:
            validate_landscape_duration(179.9)
        self.assertIn("less than the required minimum of 180.0s", str(ctx.exception))

    def test_landscape_part_bounds_enforced(self):
        """ACC-012: Part duration must satisfy 0 < d_i <= 8.0s."""
        # Test part > 8.0s rejected at construction
        with self.assertRaises(ValueError) as ctx:
            ScriptPart(
                part_number=1,
                part_type=PartType.HOOK,
                duration_seconds=8.5,
                narration_text="Too long",
                visual_cue="Cue",
            )
        self.assertIn("cannot exceed 8.0s", str(ctx.exception))

        # Test part <= 0.0s rejected at construction
        with self.assertRaises(ValueError) as ctx:
            ScriptPart(
                part_number=1,
                part_type=PartType.HOOK,
                duration_seconds=0.0,
                narration_text="Zero duration",
                visual_cue="Cue",
            )
        self.assertIn("must be strictly positive", str(ctx.exception))

    def test_landscape_sum_mismatch_rejected(self):
        """ACC-012A: Sum of parts must exactly equal total duration."""
        parts = self._build_landscape_parts(180.0)
        # Submit total duration 185.0s with 180.0s worth of parts
        with self.assertRaises(ValueError) as ctx:
            validate_landscape_duration(185.0, parts)
        self.assertIn("does not match total duration", str(ctx.exception))


class TestAspectRatioAndResolution(unittest.TestCase):
    """Test resolution mapping per ACC-008."""

    def test_vertical_resolution_1080x1920(self):
        """9:16 vertical enforces target 1080x1920."""
        valid_res = TargetResolution(width=1080, height=1920)
        validate_aspect_ratio_resolution(AspectRatio.VERTICAL_9_16, valid_res)

        invalid_res = TargetResolution(width=1920, height=1080)
        with self.assertRaises(ValueError) as ctx:
            validate_aspect_ratio_resolution(AspectRatio.VERTICAL_9_16, invalid_res)
        self.assertIn("Invalid resolution for 9:16 Vertical", str(ctx.exception))

    def test_landscape_resolution_1920x1080(self):
        """16:9 landscape enforces target 1920x1080."""
        valid_res = TargetResolution(width=1920, height=1080)
        validate_aspect_ratio_resolution(AspectRatio.LANDSCAPE_16_9, valid_res)

        invalid_res = TargetResolution(width=1080, height=1920)
        with self.assertRaises(ValueError) as ctx:
            validate_aspect_ratio_resolution(AspectRatio.LANDSCAPE_16_9, invalid_res)
        self.assertIn("Invalid resolution for 16:9 Landscape", str(ctx.exception))


class TestDEC018ExecutionEvent(unittest.TestCase):
    """Test DEC-018 metadata-only and retention invariants (ACC-030A, ACC-030B)."""

    def test_metadata_only_execution_event_succeeds(self):
        """ACC-030B: Operational metadata fields pass schema validation."""
        pid = uuid4()
        event = ExecutionEvent(
            project_id=pid,
            skill_id=SkillIdentifier.SKILL_A,
            status=JobStatus.COMPLETED,
            provider_id="gemini",
            model_id="gemini-1.5-flash",
            attempt_count=1,
            duration_ms=850.5,
            error_code=None,
            sanitized_error_message=None,
            token_usage=TokenUsage(prompt_tokens=500, completion_tokens=250, total_tokens=750),
            user_permission_granted=True,
        )
        self.assertEqual(event.project_id, pid)
        self.assertEqual(event.skill_id, SkillIdentifier.SKILL_A)
        self.assertEqual(event.duration_ms, 850.5)
        self.assertIsNotNone(event.token_usage)
        self.assertEqual(event.token_usage.total_tokens, 750)

    def test_prohibited_raw_payload_fields_rejected(self):
        """DEC-018: Raw prompts, source text, and LLM payloads are strictly rejected."""
        pid = uuid4()
        prohibited_test_cases = [
            {"raw_prompt": "Write a script about space travel"},
            {"prompt": "Generate a video hook"},
            {"source_text": "Original raw story content here"},
            {"raw_source": "Pasted raw article"},
            {"request_body": '{"model": "gpt-4"}'},
            {"raw_request": "POST /v1/chat"},
            {"response_body": '{"choices": []}'},
            {"raw_response": "Raw text completion output"},
            {"payload": "Raw generation bytes"},
            {"api_key": "sk-secret12345678"},
        ]

        for bad_kwargs in prohibited_test_cases:
            with self.subTest(prohibited=list(bad_kwargs.keys())[0]):
                with self.assertRaises(ValueError) as ctx:
                    ExecutionEvent(
                        project_id=pid,
                        skill_id=SkillIdentifier.SKILL_A,
                        status=JobStatus.RUNNING,
                        provider_id="gemini",
                        model_id="gemini-1.5-flash",
                        **bad_kwargs,
                    )
                self.assertIn("DEC-018 Security Invariant Violation", str(ctx.exception))

    def test_retention_cap_constant_defined(self):
        """ACC-030A: Retention cap is strictly 100 records per project."""
        self.assertEqual(MAX_EXECUTION_HISTORY_PER_PROJECT, 100)


class TestDEC019ProjectCap(unittest.TestCase):
    """Test DEC-019 maximum 4 active projects cap (ACC-005, ACC-006)."""

    def test_active_project_cap_constant_is_4(self):
        """DEC-019 ratified cap is strictly 4 active projects."""
        self.assertEqual(MAX_ACTIVE_PROJECTS, 4)

    def test_validate_project_cap_under_limit(self):
        """0 to 4 active projects pass validation."""
        for count in range(5):
            validate_active_project_cap(count)

    def test_validate_project_cap_exceeded_rejected(self):
        """Attempting to exceed 4 active projects raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            validate_active_project_cap(5)
        self.assertIn("Active project limit exceeded", str(ctx.exception))
        self.assertIn("maximum allowed is 4", str(ctx.exception))


class TestSingleActiveScript(unittest.TestCase):
    """Test single active script invariant per ACC-017, ACC-018."""

    def test_script_current_entity(self):
        pid = uuid4()
        parts = [
            ScriptPart(part_number=1, part_type=PartType.HOOK, duration_seconds=8.0, narration_text="N1", visual_cue="V1"),
            ScriptPart(part_number=2, part_type=PartType.STORY, duration_seconds=8.0, narration_text="N2", visual_cue="V2"),
            ScriptPart(part_number=3, part_type=PartType.ENDING, duration_seconds=8.0, narration_text="N3", visual_cue="V3"),
        ]
        script = ScriptCurrent(
            project_id=pid,
            title="Active Script",
            parts=parts,
            content_hash="sha256-abc123hash",
            source_version_used=1,
            settings_hash="sha256-settings123",
            validation_report=ValidationReport(is_valid=True),
        )
        self.assertEqual(script.project_id, pid)
        self.assertEqual(len(script.parts), 3)
        self.assertEqual(script.content_hash, "sha256-abc123hash")
        # Assert no script history attribute exists
        self.assertFalse(hasattr(script, "history"))
        self.assertFalse(hasattr(script, "prior_versions"))


class TestSEOPackage(unittest.TestCase):
    """Test YouTube SEO package invariants per ACC-024A, ACC-024B, ACC-024C."""

    def test_valid_roman_hindi_seo_package(self):
        """Valid Roman Hindi SEO package with comma-separated tags passes."""
        seo = SEOPackage(
            title="Space Travel Ki Kahani: Kaise Hua Shuru",
            description="Is video me hum jaanenge space mission ke baare me sab kuch.",
            hashtags=["#SpaceKahani", "#Vigyan", "#HindiFacts"],
            keywords=["space mission", "antariksh yatra", "vigyan ki baatein"],
            tags="space mission, antariksh, vigyan kahani, universe facts",
        )
        validate_seo_package(seo)
        self.assertIn("space mission", seo.tags)

    def test_devanagari_characters_in_seo_rejected(self):
        """ACC-024A: Devanagari Unicode in SEO fields is rejected."""
        with self.assertRaises(ValueError) as ctx:
            SEOPackage(
                title="अंतरिक्ष की कहानी (Space Story)",  # Contains Devanagari
                description="Roman Hindi description",
                hashtags=["#Space"],
                keywords=["space"],
                tags="space, mission",
            )
        self.assertIn("contains Devanagari characters", str(ctx.exception))

    def test_hashtags_or_bullets_in_tags_string_rejected(self):
        """ACC-024B: Tags string must be comma-separated without # or numbered lists."""
        with self.assertRaises(ValueError) as ctx:
            SEOPackage(
                title="Space Story Title",
                description="Space Story Description",
                hashtags=["#Space"],
                keywords=["space"],
                tags="#space, #mission, #antariksh",  # Contains #
            )
        self.assertIn("without '#' characters", str(ctx.exception))

    def test_fake_search_metrics_in_seo_rejected(self):
        """ACC-024C: Prohibit fabricated search volume metrics."""
        seo = SEOPackage(
            title="Space Story Title",
            description="This video guarantees 50,000 monthly searches volume ranking guarantee",
            hashtags=["#Space"],
            keywords=["space"],
            tags="space, mission",
        )
        with self.assertRaises(ValueError) as ctx:
            validate_seo_package(seo)
        self.assertIn("prohibited fabricated metric", str(ctx.exception))


class TestProjectAndOtherEntities(unittest.TestCase):
    """Test Project, SourceVersion, Analysis, Approval, GeneratedOutput creation."""

    def test_project_creation(self):
        """ACC-004: Project created with unique ID and settings."""
        proj = Project(
            title="My First Project",
            aspect_ratio=AspectRatio.VERTICAL_9_16,
            target_resolution=TargetResolution(width=1080, height=1920),
            duration_seconds=32.0,
            part_count=4,
            content_language=ContentLanguage.ENGLISH,
        )
        self.assertIsNotNone(proj.project_id)
        self.assertEqual(proj.title, "My First Project")
        self.assertEqual(proj.status, ProjectStatus.ACTIVE)
        self.assertEqual(proj.duration_seconds, 32.0)
        self.assertEqual(proj.part_count, 4)

    def test_source_version_creation(self):
        pid = uuid4()
        src = SourceVersion(
            project_id=pid,
            title="Source Article",
            source_type=SourceType.PASTED,
            saved_content="Some long content here...",
            content_hash="hash-12345",
            source_version=1,
            status=SourceStatus.VALIDATED,
        )
        self.assertEqual(src.project_id, pid)
        self.assertEqual(src.source_version, 1)
        self.assertEqual(src.status, SourceStatus.VALIDATED)

    def test_approval_state(self):
        pid = uuid4()
        appr = Approval(
            project_id=pid,
            script_hash="hash-script",
            settings_hash="hash-settings",
            is_approved=True,
            status=ApprovalStatus.APPROVED,
            approved_at=datetime.datetime.now(datetime.timezone.utc),
            approver_note="Approved for production",
        )
        self.assertTrue(appr.is_approved)
        self.assertEqual(appr.status, ApprovalStatus.APPROVED)

    def test_generated_output(self):
        pid = uuid4()
        out = GeneratedOutput(
            project_id=pid,
            kind=OutputKind.VIDEO_PROMPT,
            input_script_hash="hash-script",
            settings_hash="hash-settings",
            content={"prompts": [{"scene": 1, "prompt": "Cinematic shot"}]},
            validation_report=ValidationReport(is_valid=True),
        )
        self.assertEqual(out.kind, OutputKind.VIDEO_PROMPT)
        self.assertEqual(out.project_id, pid)


if __name__ == "__main__":
    unittest.main()
