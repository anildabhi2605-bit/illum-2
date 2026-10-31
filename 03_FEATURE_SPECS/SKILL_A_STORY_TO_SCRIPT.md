# Skill A — Story-to-Script Specification

## Protected contract dependency

The full original prompt is a required input to implementation. Import it from the authoritative source and store versioned/protected. Do not substitute this summary or call the skill contract complete without it.

## Purpose

Analyze user-supplied source and produce a fact-grounded script.

## Inputs

- Current project and settings.
- Saved, validated source content/version.
- Valid Source Analysis for that source version, if already available.
- Duration/part plan, aspect ratio and project content language.
- Provider/model route chosen through the shared manager.

## Process

1. Confirm source content is saved and validated.
2. Load reusable Source Analysis or create it once for current source version.
3. Analyze facts/context and preserve source traceability where possible.
4. Choose angle based on source type; plan story flow, duration and part count.
5. Generate script using the protected original contract.
6. Validate required part fields, language, structure and total duration.
7. Perform targeted corrections only where validation fails.
8. Save as a replacement candidate; overwrite latest only after candidate passes.
9. Mark approval pending and downstream actions disabled.

## Required part fields

Part number, type (Hook/Story/Ending), 8-second Hindi VO where applicable (language follows project selection), visual suggestions and on-screen text. Interpret exact fields against original prompt contract.

## Language and truthfulness

Hindi script and voiceover in Devanagari. English selection uses English. Do not invent unsupported facts. If URL cannot be read, explain why and request pasted content.

## Tests

Missing/unsaved/invalid source blocked; URL unreadable handled honestly; language checks; ratio-specific duration checks; required part fields; unsupported fact guard; validation failure preserves old script; successful candidate replaces latest; approval resets; script history not retained.
