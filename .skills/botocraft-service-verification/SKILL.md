---
name: botocraft-service-verification
description: Verify Botocraft service authoring changes by running full regeneration, inspecting generated services and docs, restarting shell-based validation, smoke-parsing representative payloads, and interpreting quality gates correctly. Use this whenever Botocraft YAML or mixins have changed and the next job is sync, inspection, smoke testing, or deciding which verification failures are real blockers.
---

# Botocraft Service Verification

Use this skill after authoring changes exist.

## Required loop

1. Run `git status --short` and re-check dirty generated-tree risk.
2. Run full `botocraft sync`, not service-scoped sync.
3. Inspect generated service module and generated docs.
4. Restart `botocraft shell` before shell-based validation.
5. Smoke parse representative payloads or imports for touched models.
6. Run focused tests plus repo-required gates that apply.

## What to look for

Catch these first:

- import and name collisions
- wrong forward references
- tag field mismatch
- wrong `response_attr`
- decorator/mixin return-shape mistakes
- live AWS enum drift encoded on only one side

## Quality-gate interpretation

Fix source-of-truth YAML and handwritten-code problems.

Do not patch generated files under `botocraft/services` only to silence style or
doc issues. Report generated-only gate noise separately.

## Useful references

Load from parent references only when needed:

- `common-manager-patterns.md`
- `model-collision-and-tags.md`
- `service-gaps-and-exceptions.md`

## Output

Verification summary should separate:

- blocking authoring errors
- follow-up candidates
- report-only generated-file noise
