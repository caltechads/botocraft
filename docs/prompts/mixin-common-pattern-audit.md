# Prompt: Audit botocraft/mixins for shared patterns

In /Users/cmalek/src/workspace/botocraft, scan handwritten mixin modules under botocraft/mixins/ for duplicated or near-duplicated helper logic that should live in the shared mixin utility module botocraft/mixins/common.py.

## Context

We already extracted two shared helpers into botocraft/mixins/common.py:

- arg_value(args, kwargs, name, position) -> Any — keyword/positional arg lookup for generated manager wrappers
- coerce_queryset_results(value) -> list[Any] — normalize PrimaryBoto3ModelQuerySet, list, or None into a plain list

Current consumers:

- botocraft/mixins/codebuild.py
- botocraft/mixins/codepipeline.py
- botocraft/mixins/codeconnections.py

Follow the same precedent as botocraft/eventbridge/common.py: small, stateless, reusable helpers for cross-service mixin code.

## Goals

1. Identify additional exact duplicates and near-duplicates across botocraft/mixins/*.py.
2. Extract only genuinely shared, general-purpose logic into botocraft/mixins/common.py.
3. Update affected mixins to import shared helpers.
4. Keep behavior unchanged.
5. Produce a follow-up plan for patterns that are similar but not yet worth extracting.

## Required preflight (before editing)

Report tool usage and one-line results for each:

- memory_search for prior mixin/common refactor context
- aidex_session + aidex_query / aidex_files as needed
- code-index search (search_code_advanced, get_symbol_body, and build_deep_index if stale)
- context7 / package-registry only if external library behavior matters; otherwise say not relevant

## What to search for

Scan all files in botocraft/mixins/*.py for patterns like:

### Arg/context extraction

- Keyword vs positional lookup beyond simple arg_value
- Reattaching call-context fields to listed results (pipelineName, RegistryName, projectName, etc.)
- Model-first arg inference (args[0], kwargs["model"], attribute fallback)

### Queryset/list normalization

- if not isinstance(results, PrimaryBoto3ModelQuerySet): results = PrimaryBoto3ModelQuerySet(results)
- isinstance(x, PrimaryBoto3ModelQuerySet) then .results
- hasattr(qs, "results") duck-typing
- None -> [] or empty queryset handling

### Response shaping

- response.model_dump(exclude_none=True) + nested key unwrap (payload.get("foo", payload))
- if response is None: return None
- if isinstance(response, TargetModel): self.sessionize(response); return response
- Re-fetch-after-empty-update patterns

### Batch/chunk helpers

- Fixed-size chunking over string lists/ARNs/IDs
- Repeated for chunk in ...: client.batch_get_*

### Sessionization/queryset rebuild

- PrimaryBoto3ModelQuerySet(...) + self.sessionize(...)
- List comprehension rebuild + re-wrap as queryset

## Classification rules

For each candidate, classify as:

- Extract now — exact duplicate or clearly general helper with 2+ call sites and stable semantics
- Defer — near-duplicate but domain-specific or only 1–2 sites; note why
- Not appropriate — service-specific workflow, different contract (required arg + raise), or would over-generalize

Do not extract:

- CodeBuild-only _chunked unless duplicated elsewhere
- Schemas-style required-arg helpers like _registry_name_from_call
- Domain transforms (EC2 reservation flattening, ECS .clusters access, tag hydration classes)

## Repository constraints (must follow)

From AGENTS.md:

- Do not edit generated code under botocraft/services/
- Handwritten changes only in botocraft/mixins/ and related tests/docs if needed
- Prefer direct, human-comprehensible helpers/classes over scattered one-off logic
- Maintain Napoleon/docstring contract for non-test Python
- If botocraft.sync changes seem necessary, stop and ask before editing

## Implementation expectations

1. Add helpers to botocraft/mixins/common.py with public names unless privacy is clearly better.
2. Candidate new helpers to evaluate first:
   - ensure_queryset(value) -> PrimaryBoto3ModelQuerySet
   - shared nested-response payload extraction
   - shared chunking helper if duplicated
   - shared reattach-context-field-to-listed-models helper only if semantics truly match
3. Update imports/usages in affected mixins.
4. Avoid unrelated refactors.
5. Add tests only if they cover meaningful new behavior; skip trivial import-only tests.

## Likely starting points (verify, do not assume)

Prior analysis flagged these as follow-up candidates:

- botocraft/mixins/codepipeline.py — queryset ensure/wrap + possible coerce_queryset_results iteration
- botocraft/mixins/schemas.py — queryset ensure/wrap
- botocraft/mixins/ecs.py — queryset unwrapping with non-.results attrs
- botocraft/mixins/ec2.py — reservation flattening
- botocraft/mixins/codebuild.py — repeated response-to-model wrapper structure

Re-evaluate all mixins fresh; do not limit scope to these files.

## Deliverables

1. Findings table grouped as: extract now / defer / not appropriate
2. Implementation for extract-now items
3. Summary:
   - new helpers added to common.py
   - files updated
   - duplicates removed
   - deferred candidates with reasons
4. Verification on touched files:
   - ruff
   - mypy (at least --follow-imports=skip on touched files)
   - make napoleon-gate
   - targeted pytest for affected services
   - clearly separate pre-existing unrelated gate failures

Verification commands:

    .venv/bin/ruff check botocraft/mixins/common.py botocraft/mixins/<touched>.py
    .venv/bin/mypy --follow-imports=skip botocraft/mixins/common.py botocraft/mixins/<touched>.py
    make napoleon-gate
    .venv/bin/pytest tests/services/test_<service>.py -q

## Output format

Start with a short audit summary, then implement extractions in small commits-worth of changes, then finish with:

    ## Extracted
    - helper_name: purpose, files updated

    ## Deferred
    - pattern: location, reason

    ## Not appropriate
    - pattern: location, reason

Prioritize correctness and minimal diff over aggressive abstraction.
