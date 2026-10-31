# Skill B — Script-to-Video Prompt Engineering Specification

## Protected contract dependency

Import/version the authoritative original Skill B prompt first. This document is a requirements map, not a replacement prompt.

## Purpose and boundaries

Convert current approved script into detailed video-generation prompts for each part. It creates prompts, not actual video files.

## Inputs

- Current approved script and exact script hash/version.
- Current project ID/settings, ratio, duration plan, content/voiceover language.
- Valid Script Analysis for current script version.
- Current provider/model route.

## Process

1. Enforce current approval on backend.
2. Verify script and settings freshness.
3. Reuse valid Script Analysis; re-run only if invalid/stale/missing or user asks.
4. Analyze action, facts, scene, timeline, camera, lighting, style, audio, continuity and constraints for each part.
5. Generate one prompt per script part.
6. Validate each prompt and ratio/language/part constraints; targeted corrections only.
7. Save only after all required validation passes, or follow the original contract's exact partial-result rules if any.

## Required constraints

- Preserve script meaning; do not invent events, people or facts.
- Respect selected aspect ratio and voiceover/content language.
- No part duration beyond project's rules (no greater than 8 seconds for landscape; exactly 8 seconds for approved vertical parts).
- Return prompts and validation report according to original contract.

## Tests

Blocked if current approval missing/stale; reuse analysis; invalidation after script edit; one prompt per part; duration/ratio/language checks; no unsupported scene additions; schema validation; previous valid outputs preserved on failure.
