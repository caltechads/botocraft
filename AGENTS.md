# AGENTS.md

- use .venv/bin/python as python
- use .venv/bin/pytest as pytest
- use .venv/bin/ruff as ruff
- use .venv/bin/mypy as mypy
- use `uv add <package>` to add a core package
- use `uv add --group=test <package>` to add a test package
- use `uv add --group=docs <package>` to add a docs package
- use `uv add --group=dev <package>` to add a dev-only package

## Tooling Preflight (Required)

Before planning or implementation, show concise evidence of:

1. `graphify` for prior context and codebase exploration
2. At least one `code-index` call (search/find/symbol/summary as useful)
3. `context7` and/or `package-registry-mcp` when external library/package behavior, versioning, or package details matter

In an early progress update: tool names used + one line per result. If a tool is not relevant, say so in one line.

During planning, please use `graphify` and `code-index` often to flesh out plans.

In an early progress update, include the tool names used and one line on what each returned.
If a tool is not relevant for the task, state that explicitly in one line.

## Post-Implementation Quality Gate (Required)

After implementation edits:

1. `ruff` on touched files (or broader if needed)
2. `.venv/bin/mypy` on touched files (or broader if needed)
3. `make napoleon-gate`
4. Fix all reported problems before finishing

## Implementation Priority (Required)

Implement the correct product code directly. Do not add runtime patching, indirection, monkey-patching, startup hooks, or similar workarounds just to dodge doc-gate noise, baseline drift, or other documentation-tool friction.

1. Put the change in the correct source file, even when that file has noisy docs or baseline issues
2. Report quality-gate blockers separately, noting pre-existing or unrelated failures
3. Architecture and correctness beat avoiding documentation churn

## Generated Service Boundaries (Required)

When debugging or implementing service behavior in this repository:

1. Do not edit anything under `botocraft.services`. That code is generated and
   will be overwritten.
2. Make service-behavior changes in handwritten code under `botocraft.mixins`
   and service configuration under `botocraft/data`, then regenerate services.
3. If you believe `botocraft.sync` must change, stop and explain the proposed
   change to the user before editing it. Do not proceed without explicit user
   approval.

## Human-Comprehensible Architecture Preference (Required)

For most non-trivial behavior in this repository, prefer implementing cohesive,
human-comprehensible classes over large collections of loosely related free
functions, even when those classes are mostly stateless.

Reason:

1. Clear class responsibilities and interactions make it easier for humans to
   cognitively model the system.
2. Prefer classes that represent real workflow boundaries, owned
   responsibilities, or stable concepts in the domain.
3. Avoid creating classes that are just arbitrary namespaces, but when the
   alternative is a mass of individual functions with shared implicit context,
   prefer the class-oriented design.
4. Favor constructor injection and explicit collaborators when that improves
   readability and makes the system easier for humans to follow.

## Documentation Contract (Required)

For all non-test Python code in this repository:

1. Class docstrings must describe the class contract and include constructor `Args:` when constructor arguments exist.
2. Function/method docstrings must include:
   - brief description
   - `Side Effects:` (only when there are real side effects; omit otherwise)
   - `Args:` (only when positional args exist; omit otherwise)
   - `Keyword Args:` (only when keyword args exist; omit otherwise)
   - `Raises:` (only when meaningful exceptions are raised; omit otherwise)
   - `Returns:` or `Yields:` (only when applicable; omit otherwise)
   - Do not add placeholder content such as `None.` for empty/inapplicable sections.
   - Never add `Args:`/`Keyword Args:`/`Returns:`/`Yields:` sections when they would be empty or semantically `None`.
3. Document all of the following with Napoleon `#:` comments:
   - class attributes
   - instance attributes assigned in `__init__`
   - module-level global variables

Enforcement command:

- `make napoleon-gate` (no new violations vs baseline)
- `make napoleon-gate-strict` (all violations; use when explicitly requested)

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
