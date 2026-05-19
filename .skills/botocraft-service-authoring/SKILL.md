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

## AWS docs preference

When AWS service semantics, field meaning, operation behavior, or relation
guessing needs external docs:

- prefer `aws-knowledge-mcp-server` if it is available in the current tool set
- check available tools or tool discovery before falling back to generic search
- if `aws-knowledge-mcp-server` is not installed, say so plainly and ask
  whether the user wants to install it
- if the user says no, continue with web search against official AWS docs
  instead of blocking
- prefer official AWS domains such as `docs.aws.amazon.com`,
  `boto3.amazonaws.com`, and `botocore.amazonaws.com`
- do not repeatedly re-ask about installation in the same task once the user
  has declined

Example:

> I don't have `aws-knowledge-mcp-server` in this session. Do you want to
> install it? If not, I'll continue with official AWS docs on the web.

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
- `generator-yaml-pitfalls.md` (empty output, `Return`, `response_attr`, collisions)
- `model-collision-and-tags.md`
- `relation-discovery.md`
- `relations-properties-bespoke.md`
- `ec2-case-study.md`
- `service-gaps-and-exceptions.md`
- `monolith-snapshot.md` when comparing against old single-skill baseline

Prefer one reference first. Load more only when task clearly crosses domains.

## Relation workflow

When task includes identifying, proposing, reviewing, or implementing
`relations:` for primary models, use a two-stage workflow:

1. discovery and review
2. implementation after user approval

Stage 1 must:

- inspect primary-model fields and nested shapes for likely foreign identifiers
- use AWS docs when needed for fuzzy or non-obvious relationships
- produce candidate relations with confidence and evidence
- stop for user keep/drop review before editing YAML

Stage 2 must:

- implement only approved relations
- leave rejected or low-confidence candidates as raw identifiers or properties
- explain why any candidate was not implemented

Do not jump straight from "I found a likely relation" to editing `models.yml`
unless the user explicitly says to skip review.

## Decision pauses

Ask user only when repo inspection cannot settle a meaningful product tradeoff.
Typical real pauses:

- multiple plausible primary resources
- shape-backed vs bespoke model
- readonly vs writable public contract
- relation vs property vs leave raw identifier
- keep/drop review of suggested relations
- decorator vs manager mixin when both are credible

Do not ask questions that botocore, repo patterns, or generator behavior can
answer directly.

## Global rules

- Author source of truth in `botocraft/data/<service>/models.yml` and
  `botocraft/data/<service>/managers.yml`.
- In `managers.yml`, manager keys must use the botocore shape name from the
  model definition key, not the public `alternate_name`.
- Put handwritten helpers in `botocraft/mixins/<service>.py`.
- Do not hand-edit generated files in `botocraft/services/` or generated docs.
- Prefer direct source-of-truth fixes over runtime workarounds.
- Keep first pass narrow: one or two high-confidence primary models.
- Prefer the narrow resource or summary shape as the primary model when
  `get()` or `list()` can hydrate it cleanly.
- Do not use wrapper response classes such as `Get*Response` as the primary
  model when a nested shape or summary shape represents the actual resource.
- Keep richer wrapper response classes only when the narrower shape would lose
  required fields needed for the supported create, update, or get surface.
- `.get()` and `.list()` should return model instances, not raw identifiers.
- Normalize Botocraft tag field names to `Tags`.
- For non-CRUD manager methods, follow `generator-yaml-pitfalls.md` for
  `return_type` / `response_attr`; inspect generated `botocraft/services/` code
  after sync.

## Output expectations

By end of task, summary should name:

- chosen leaf skills and references
- first primary models and why
- authored methods, relations, properties, mixins, or decorators
- any unresolved human choices
- verification results and any report-only generated-file gate noise
