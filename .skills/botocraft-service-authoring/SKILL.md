---
name: botocraft-service-authoring
description: Add support for a new AWS service in Botocraft by inspecting botocore models, authoring botocraft/data/<service>/models.yml and managers.yml, adding mixins or decorators only when generation is not enough, regenerating all services, and asking the user to choose whenever there are meaningful modeling or API tradeoffs. Use this whenever the user asks to add support for an AWS service, build out Botocraft support for a service, author a new Botocraft service, scaffold service definitions, or extend Botocraft's AWS surface, even if they do not explicitly mention skills.
---

# Botocraft Service Authoring

Use this skill when the user wants Botocraft to support a new AWS service.
This is a repo-specific authoring workflow, not a generic AWS SDK task.

The goal is to produce maintainable Botocraft service definitions that feel
natural at the object layer and survive full regeneration cleanly.

## Operating Contract

Inspect first, then implement.

Do not jump straight into YAML edits after seeing a service name. First inspect:

- the botocore service alias
- the raw botocore shapes
- candidate primary models
- existing Botocraft patterns that are closest to this service

Ask the user concise questions whenever there are real choices that materially
change the authored API. In this repository, that usually means:

- multiple plausible botocore service aliases
- several plausible primary models and no obvious first choice
- a model that could be readonly or CRUDL-capable
- bespoke model vs shape-backed model
- relation vs plain property vs leaving raw identifier data alone
- decorator vs manager mixin vs handwritten manager method
- convenience methods whose ergonomics are subjective rather than obvious

Do not ask questions that the repository or botocore inspection can answer.

## Required Repo Preflight

Before authoring, provide concise evidence of:

1. `memory_search` for prior Botocraft context.
2. At least one `aidex` call. If AiDex is broken in the environment, say so
   explicitly and continue with direct repo inspection.
3. At least one `code-index` call for generator or CLI touchpoints.
4. `context7` when current boto3 or botocore behavior is relevant.

Also inspect these repo references before making decisions:

- `doc/source/runbook/authoring.rst`
- `doc/source/runbook/service_authoring_reference.rst`
- `botocraft/data/ecs/models.yml`
- `botocraft/data/ecs/managers.yml`
- `botocraft/data/s3/models.yml`
- `botocraft/data/s3/managers.yml`
- `botocraft/mixins/ecs.py`
- `botocraft/mixins/s3.py`

Use those files as the default patterns instead of inventing a new style.

## Core Rules

Follow these Botocraft-specific rules:

- Author source of truth in `botocraft/data/<service>/models.yml` and
  `botocraft/data/<service>/managers.yml`.
- Put handwritten helpers only in `botocraft/mixins/<service>.py`.
- Do not hand-edit generated files in `botocraft/services/` or generated docs.
- Always run full `botocraft sync`, not just service-scoped sync, after
  meaningful authoring changes.
- Run `botocraft shell` after sync to catch import and forward-reference issues.

Object API rules:

- `.get()` and `.list()` should return model instances, not raw names or ARNs.
- If AWS returns identifiers from a list operation, prefer a decorator that
  converts them into model instances.
- `.create()` should take the model instance as the primary parameter, with
  extra keyword args only when truly required by the AWS API.
- Read-only resources should expose read/list-oriented managers instead of fake
  write methods.
- Use manager shortcut methods on models when an operation is naturally scoped
  to the instance.

Modeling rules:

- Start with one or two high-confidence primary models. Expand only after sync
  succeeds and the generated API looks healthy.
- Prefer shape-backed models plus targeted overrides before reaching for
  `bespoke: true`.
- Use `input_shapes` as the main source of writability inference.
- Use `output_shape` when get/list responses add fields that are useful on the
  object but absent from the base shape.
- Infer useful relations from model attributes when there is a stable manager
  lookup path to another primary model.
- Prefer simple YAML properties for derived data. Escalate to a model mixin
  only when the behavior needs real Python logic.
- Prefer mapping-based relations. Treat regex-backed relations as exceptional,
  not the default path.

Collision and typing rules:

- Check for cross-service model name collisions before finalizing public names.
- Resolve collisions with `alternate_name`, field `rename`, or targeted type
  overrides.
- Be alert for field/type equality problems where a field's inferred type name
  matches the field name itself. Those often need `alternate_name` or field
  renaming to avoid generator failures.
- If the service alias contains a hyphen, remember that the generated module
  name uses underscores.

## Workflow

### 1. Confirm the service target

If the user gave a plain English AWS service name, discover the botocore alias.
Use the alias as the canonical service directory name under `botocraft/data/`.

If more than one alias is plausible, stop and ask the user which one they want.

### 2. Inspect botocore before authoring

Use the CLI workflow from the runbook:

- `botocraft botocore services`
- `botocraft botocore models <service>`
- `botocraft botocore model <service> <shape> --dependencies --operations`
- `botocraft botocore primary-models <service>`

Use this pass to identify:

- real resources vs nested helper structures
- likely CRUDL models
- likely read-only models
- list operations that return identifiers instead of full objects
- input/output shape mismatches
- likely secondary models that may need overrides or renames

### 3. Choose the first primary models

Prefer starting with one or two primary models that have most of these traits:

- clear resource identity
- at least `get` or `list` style operations
- understandable request and response shapes
- a plausible primary key and, ideally, ARN or name fields

If the service has several plausible entry points, ask the user to choose the
first scope rather than authoring the whole service blindly.

### 4. Author `models.yml`

Start with the smallest useful definition set.

For each primary model, determine:

- `primary_key`
- `arn_key` when present
- `name_key` when present
- `input_shapes`
- `output_shape` when needed
- field overrides
- properties
- relations
- `manager_methods`
- model mixins only if YAML is not enough

Only add explicit secondary model configuration when it materially improves the
generated output, such as:

- `alternate_name`
- `force_create`
- field overrides
- better nested type behavior
- mixins or properties on secondary models

### 5. Author `managers.yml`

For each primary model, prefer generated methods first:

- `get`
- `list`
- `create` when creation is natural
- `update` or `partial_update` when the API supports it
- `delete` when deletion is supported

For read-only resources, prefer `get`, `get_many`, `list`, and other clearly
useful read helpers instead of forcing CRUDL symmetry.

Check for each method:

- correct `boto3_name`
- correct `response_attr`
- argument overrides that line up with the input shape
- return behavior that yields model instances when appropriate

Add other useful manager methods only when they provide genuine ergonomic value,
such as:

- family or namespace lookups
- service-specific list variants
- instance-scoped helpers that the model should expose through
  `manager_methods`

### 6. Decide when handwritten code is necessary

Use a property when a small YAML transformer is enough.

Use a relation when the object should naturally resolve to another primary
resource and a stable lookup path exists.

Use a decorator when the generated AWS call is basically correct but the return
value needs reshaping, especially when:

- a list returns identifiers and should return model instances
- a response needs light post-processing
- a missing-result exception should become an expected empty result
- batching is needed around an AWS per-call limit

Use a manager mixin when:

- a method requires multiple AWS API calls
- the AWS API is too irregular for generated methods to feel natural
- the manager needs higher-level workflows beyond direct boto3 wrappers

Use a model mixin when:

- behavior belongs on the object
- logic depends on several fields or related resources
- the YAML property system would become contorted

### 7. Regenerate and smoke test

After authoring changes:

1. Run full `botocraft sync`.
2. Inspect the generated service module and generated service docs.
3. Run `botocraft shell`.
4. Fix naming, import, type, relation, or collision issues before expanding the
   service further.

Do not skip full regeneration. Cross-service collisions are part of normal
authoring in this repository.

### 8. Summarize clearly

At the end, summarize:

- which primary models were added first
- which methods were authored
- which relations, properties, mixins, and decorators were added
- any unresolved follow-up candidates for later expansion
- any questions that still need a human decision

## Decision Defaults

When the repository evidence does not force a different answer, prefer:

- YAML-first authoring
- direct product-code changes over workaround architecture
- generated CRUDL or read/list methods before handwritten logic
- decorators over heavier manager rewrites for list/get result reshaping
- mapping relations over regex relations
- one or two primary models first, not maximal first-pass scope
- object methods only when they are clearly instance-scoped and ergonomic

## Example Requests

- "Add Botocraft support for AWS Backup."
- "Build out Botocraft support for the AWS Glue Data Catalog service."
- "Author a new Botocraft service for AWS Bedrock Agents, starting with the
  read-only resources."
- "Add support for an AWS service where list returns ARNs and make sure list
  returns model instances."

## Out of Scope

This skill is primarily for adding a brand-new AWS service.

You can reuse the same workflow for adding another model to an existing service,
but do not treat that as the primary trigger or main description of the skill.
