# Skill C — AI Thumbnail Intelligence Specification

## Protected contract dependency

Import/version original Skill C prompt from authoritative source first.

## Purpose

Produce exactly one complete image-generation prompt for the current project thumbnail. It does not generate the image file.

## Primary input

Entire current approved final script — not only the hook or selected individual parts — plus aspect ratio and thumbnail text language.

## Process

1. Enforce approval and freshness.
2. Read whole script and relevant analysis if valid.
3. Choose a compelling but truthful central visual idea.
4. Specify subject, composition, background, lighting, style and optional text where useful.
5. Apply project's aspect ratio and selected thumbnail text language.
6. Validate one complete prompt and save only when valid.
7. Regenerate/revalidate when source script or dependent settings make prompt stale.

## Tests

Must use entire current script; exactly one complete prompt; no misleading claim; correct ratio; Hindi thumbnail text in Devanagari or English as selected; output invalidated on script/settings change; no prompt generation when approval missing/stale.
