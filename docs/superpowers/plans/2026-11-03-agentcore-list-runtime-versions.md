# AgentCore `list_versions` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A caller can iterate every version of an AgentCore Runtime through `AgentCoreAgentRuntimeManager.list_versions(agentRuntimeId)`, which returns a `PrimaryBoto3ModelQuerySet`, with no raw boto3.

**Architecture:** The generator only emits a `PrimaryBoto3ModelQuerySet` for `list` and `get_many`; any other generated list method returns a plain `list` (see iam and schemas `list_versions`). So `list_versions` is a handwritten manager mixin class, wired to the `AgentRuntime` manager in `managers.yml`. The `ListAgentRuntimeVersions` item shape is `AgentRuntime`, already the primary model `AgentCoreAgentRuntime`, so no model change is needed. No `botocraft.sync` change.

**Tech Stack:** botocraft YAML generator (`botocraft sync`), botocore paginator, pytest with botocore `Stubber` (offline).

**Spec:** Trello card https://trello.com/c/SjdUa62U/65-agentcore-list-runtime-versions-listagentruntimeversions (no separate spec file). Owner decisions: return type must be `PrimaryBoto3ModelQuerySet`; release is patch version 0.36.2; mypy on the main files is the priority, and test files may use `pyproject.toml` suppressors and `noqa`.

## Global Constraints

- Never edit `botocraft/services/` (generated). Config goes in `botocraft/data/bedrock-agentcore-control/managers.yml`; behavior goes in `botocraft/mixins/`.
- Do not change `botocraft.sync`; if it seems necessary, stop and ask the owner.
- Tests run offline (Stubber or moto). No live AWS calls, and no secrets or account IDs in code, tests, fixtures or docs.
- Use `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`, `.venv/bin/mypy`.
- Branch before committing. Do not push.
- Mixin code needs the AGENTS.md docstring contract (class docstring with constructor `Args:` if any, Napoleon `#:` comments for attributes and module globals) and must be a cohesive class, not loose functions.
- Method name `list_versions` follows the schemas, grafana and iam precedent.

## Review Focus

- An empty page that still carries a `nextToken` does not end iteration (the mixin must not `break` on an empty page).
- Page 1 has items and a token, page 2 has items and no token: all items are returned, in order.
- Empty first page with no token returns an empty `PrimaryBoto3ModelQuerySet`, not a plain list and not an error.
- `agentRuntimeId` omitted raises `TypeError`, and the id is passed to boto3 unchanged.
- `lastUpdatedAt` is parsed into `datetime` and `status` into the model's `Literal`; items are `AgentCoreAgentRuntime` instances and the manager is session-bound (`sessionize` called on results).

---

### Task 1: Mixin and wiring

**Files:**
- Create: `botocraft/mixins/bedrock_agentcore_control.py`
- Modify: `botocraft/data/bedrock-agentcore-control/managers.yml` (add `mixins:` to the `AgentRuntime` block; no `list_versions` method entry, which would collide with the mixin)
- Regenerated (do not hand-edit): `botocraft/services/bedrock_agentcore_control.py`, generated docs

**Interfaces:**
- Produces: `class AgentCoreAgentRuntimeManagerMixin` with `list_versions(self, agentRuntimeId: str) -> PrimaryBoto3ModelQuerySet`. After sync, `AgentCoreAgentRuntimeManager` inherits it.

- [ ] **Step 1: Confirm a clean tree and branch**

Run: `git status --short` (expect no output), then `git switch -c feature/agentcore-list-runtime-versions`.

- [ ] **Step 2: Read the wiring precedent**

Read how `ConversationManagerMixin` in `botocraft/mixins/bedrock_runtime.py` is declared and how `botocraft/data/bedrock-runtime/managers.yml` references it under `mixins:`. Check how another mixin gets the model class without a circular import (it imports `botocraft.services...` inside the method).

- [ ] **Step 3: Implement `AgentCoreAgentRuntimeManagerMixin.list_versions(self, agentRuntimeId: str) -> PrimaryBoto3ModelQuerySet`** in `botocraft/mixins/bedrock_agentcore_control.py`.
  - Use `self.client.get_paginator("list_agent_runtime_versions")` and iterate all pages; extend results from each page's `agentRuntimes` and never `break` on an empty page.
  - Build each item as `AgentCoreAgentRuntime`, call `self.sessionize(results)`, and return `PrimaryBoto3ModelQuerySet(results)`, including for an empty result.
  - Follow the generated `list()` for the `ResponseMetadata` handling. Include a docstring with `Args:` and `Returns:`, and `#:` comments on any attributes.

- [ ] **Step 4: Wire it in YAML** under `AgentRuntime`:

```yaml
  mixins:
    - name: AgentCoreAgentRuntimeManagerMixin
      import_path: botocraft.mixins.bedrock_agentcore_control
```

- [ ] **Step 5: Regenerate**

Run: `.venv/bin/botocraft sync` (full sync, per `doc/source/runbook/authoring.rst`).
Expected: the diff touches only `bedrock_agentcore_control` generated files and their docs. If other services change, stop and report the drift.

- [ ] **Step 6: Confirm the generated manager**

Run: `grep -n "class AgentCoreAgentRuntimeManager" -A3 botocraft/services/bedrock_agentcore_control.py`
Expected: the class lists `AgentCoreAgentRuntimeManagerMixin` as a base, and `list_versions` is not generated in the file.

- [ ] **Step 7: Commit**

```bash
git add botocraft/mixins/bedrock_agentcore_control.py botocraft/data/bedrock-agentcore-control/managers.yml botocraft/services doc
git commit -m "FEATURE: add AgentCoreAgentRuntimeManager.list_versions"
```

### Task 2: Tests

**Files:**
- Create: `tests/services/test_bedrock_agentcore_control.py` (append instead if it exists)
- Modify (only if mypy needs it): `pyproject.toml` per-module overrides for the test file

**Interfaces:**
- Consumes: `AgentCoreAgentRuntimeManager().list_versions(agentRuntimeId: str) -> PrimaryBoto3ModelQuerySet` from Task 1.

- [ ] **Step 1: Write the tests**, attaching a botocore `Stubber` to the manager's client as `tests/services/test_bedrock.py` does:
  - `test_list_versions_paginates_two_pages`: page 1 has two versions plus `nextToken`, page 2 has one version and no token; assert 3 results, in order, with `agentRuntimeId` as the expected param.
  - `test_list_versions_empty_page_with_token_continues`: page 1 is empty with a token, page 2 has one version; assert 1 result.
  - `test_list_versions_empty`: `agentRuntimes: []`; assert `isinstance(result, PrimaryBoto3ModelQuerySet)` and length 0.
  - `test_list_versions_returns_typed_models`: every item is an `AgentCoreAgentRuntime` with `agentRuntimeVersion`, `status`, and a `datetime` `lastUpdatedAt`; the result is a `PrimaryBoto3ModelQuerySet`.
  - `test_list_versions_requires_runtime_id`: calling with no argument raises `TypeError`.
  - Use fake ids such as `rt-example` and the account `000000000000` in ARNs.

- [ ] **Step 2: Run**

Run: `.venv/bin/pytest tests/services/test_bedrock_agentcore_control.py -v`
Expected: 5 passed. Prove the tests can fail: temporarily add a `break` on empty pages in the mixin, confirm `test_list_versions_empty_page_with_token_continues` fails, then restore.

- [ ] **Step 3: Commit**

```bash
git add tests/services/test_bedrock_agentcore_control.py pyproject.toml
git commit -m "TEST: cover AgentCoreAgentRuntimeManager.list_versions"
```

### Task 3: Version, changelog, docs and quality gate

**Files:**
- Modify: `CHANGELOG.md` (new `## [0.36.2] - <date>` section with `### Added`, matching the existing prose style)
- Modify: the version files the repo's bump tooling manages (find them from the bump config in `pyproject.toml` or `.bumpversion.*`), only through that tooling
- Modify: hand-written docs only if a page lists AgentCore runtime methods (`grep -rn "AgentCoreAgentRuntime" doc/source --include=*.rst`)

- [ ] **Step 1: Add the changelog entry**: "Add `AgentCoreAgentRuntimeManager.list_versions(agentRuntimeId)` to list every version of an AgentCore Runtime, across all result pages. It returns a queryset of `AgentCoreAgentRuntime` items with `agentRuntimeVersion`, `status` and `lastUpdatedAt`."

- [ ] **Step 2: Bump to 0.36.2** with the repo's bump command (read its config first; if it makes its own commit, accept that as the version commit). Confirm the version string reads `0.36.2` everywhere the config lists.

- [ ] **Step 3: Run the gates and fix everything reported**

Run in order:
- `.venv/bin/ruff check botocraft/mixins/bedrock_agentcore_control.py tests/services/test_bedrock_agentcore_control.py`
- `.venv/bin/mypy botocraft/mixins/bedrock_agentcore_control.py botocraft/services/bedrock_agentcore_control.py` (main files must be clean), then mypy on the test file (suppress through `pyproject.toml` overrides or `noqa` only for the test file)
- `make napoleon-gate`
- `.venv/bin/pytest`
Expected: all clean, or only failures that existed before this branch (record those separately).

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md doc
git commit -m "DOCS: changelog for AgentCore list_versions"
```

- [ ] **Step 5: Update the graph**

Run: `graphify update .`
