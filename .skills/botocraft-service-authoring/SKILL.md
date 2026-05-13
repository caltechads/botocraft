---
name: botocraft-service-authoring
description: Coordinate Botocraft AWS service authoring by doing repo preflight, checking dirty generated-tree risk, choosing the correct authoring leaf skill, and routing to focused references instead of carrying every edge case inline. Use this whenever the user wants to add a new AWS service to Botocraft, expand an existing Botocraft service, scaffold `models.yml` or `managers.yml`, inspect botocore shapes for Botocraft authoring, or reason about service-authoring tradeoffs, even if they do not explicitly mention skills.
---

# Botocraft Service Authoring

Use this skill as router and guardrail for Botocraft service authoring.
Do repo-specific setup here, then load one focused leaf skill first.

## First moves

Before planning or editing, provide concise preflight evidence for:

1. `memory_search` for prior Botocraft context.
2. At least one `aidex` call. If AiDex is broken, say so explicitly and fall
   back to direct repo inspection.
3. At least one `code-index` call for generator, mixin, or CLI touchpoints.
4. `context7` when current boto3 or botocore behavior matters.

Also inspect:

- `doc/source/runbook/authoring.rst`
- `doc/source/runbook/service_authoring_reference.rst`
- one strong service pattern pair from `botocraft/data`
- one strong handwritten mixin example when decorators or mixins seem likely

In an early progress update, name each preflight tool and what it returned.

## Dirty-tree safeguard

Run `git status --short` before reasoning about regeneration.

If generated services or generated docs are already dirty:

- pause before proposing full `botocraft sync`
- explain why generated-tree churn makes service authoring hard to reason about
- ask user to confirm checkpoint/stash/continue only when sync is actually next

Do not pretend service-scoped reasoning is safe when full sync would rewrite
many already-dirty generated files.

## Routing rule

Load exactly one core leaf skill first:

- `../botocraft-service-discovery/SKILL.md`
- `../botocraft-model-authoring/SKILL.md`
- `../botocraft-manager-authoring/SKILL.md`
- `../botocraft-service-verification/SKILL.md`

Escalate to an advanced leaf only when concrete signals appear:

- collisions, `alternate_name`, field/type-name conflicts
- properties, relations, composite `pk`, or bespoke models
- decorators, manager mixins, identifier-only lists, context-required list/get
- two-step disable/delete flows or irregular non-CRUD methods

Advanced leaves:

- `../botocraft-model-advanced/SKILL.md`
- `../botocraft-manager-advanced/SKILL.md`

## Leaf selection heuristics

Start with `botocraft-service-discovery` when task is still about:

- botocore alias
- likely primary models
- readonly vs CRUDL classification
- first safe scope
- manager naming or operation inventory

Start with `botocraft-model-authoring` when task is mainly about:

- `models.yml`
- `primary_key`, `arn_key`, `name_key`
- `input_shapes`, `output_shape`
- field overrides or `Tags`

Start with `botocraft-manager-authoring` when task is mainly about:

- `managers.yml`
- `get`, `list`, `create`, `update`, `delete`
- return-shape decisions
- readonly/writable/updatable manager contract

Start with `botocraft-service-verification` when YAML already exists and task is
about regeneration, inspection, smoke testing, or quality gates.

## Reference loading

Do not keep catalogs inline. Load only needed references from `references/`:

- `common-manager-patterns.md`
- `model-collision-and-tags.md`
- `relations-properties-bespoke.md`
- `ec2-case-study.md`
- `service-gaps-and-exceptions.md`
- `monolith-snapshot.md` when comparing against old single-skill baseline

Prefer one reference first. Load more only when task clearly crosses domains.

## Decision pauses

Ask user only when repo inspection cannot settle a meaningful product tradeoff.
Typical real pauses:

- multiple plausible primary resources
- shape-backed vs bespoke model
- readonly vs writable public contract
- relation vs property vs leave raw identifier
- decorator vs manager mixin when both are credible

Do not ask questions that botocore, repo patterns, or generator behavior can
answer directly.

## Global rules

- Author source of truth in `botocraft/data/<service>/models.yml` and
  `botocraft/data/<service>/managers.yml`.
- Put handwritten helpers in `botocraft/mixins/<service>.py`.
- Do not hand-edit generated files in `botocraft/services/` or generated docs.
- Prefer direct source-of-truth fixes over runtime workarounds.
- Keep first pass narrow: one or two high-confidence primary models.
- `.get()` and `.list()` should return model instances, not raw identifiers.
- Normalize Botocraft tag field names to `Tags`.

## Output expectations

By end of task, summary should name:

- chosen leaf skills and references
- first primary models and why
- authored methods, relations, properties, mixins, or decorators
- any unresolved human choices
- verification results and any report-only generated-file gate noise
