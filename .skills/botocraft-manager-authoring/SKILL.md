---
name: botocraft-manager-authoring
description: Author Botocraft `managers.yml` for core manager contracts by choosing readonly versus writable manager shape, implementing `get`, `list`, `create`, `update`, `partial_update`, `delete`, and `get_many`, and ensuring methods return Botocraft model instances instead of raw AWS payloads. Use this whenever the user is designing Botocraft managers or asking how boto3 operations should map into Botocraft manager methods.
---

# Botocraft Manager Authoring

Use this skill for common-path `managers.yml` work.

## Manager naming

Manager should attach to chosen public primary model name.
If model uses `alternate_name`, manager follows public name, not raw shape name.

## Contract classification

Classify manager before writing methods:

- readonly: `get` + `list`, maybe `get_many` or read helpers
- writable not updatable: `create`, `get`, `list`, maybe `delete`
- fully modifiable: `create`, `get`, `list`, `update`, `delete`

`partial_update` is rare. Use only when API naturally supports field-oriented
patch behavior better than full model resubmission.

## Required baseline

Every normal primary model should aim for:

- `get`
- `list`

If writable, add `create`, `update`, `delete` when AWS API makes them natural.

## `get` patterns

Common repo patterns:

- singular Botocraft arg mapped to plural AWS ID list on `describe_*`
- plain `get_*` operation with `response_attr`
- `describe_*` plus `response_attr`

Use singular Botocraft arg names even when boto3 expects one-item list, as long
as generator can transform it cleanly.

## `list` patterns

Common repo patterns:

- paginated `describe_*` returning full objects
- `list_*` returning direct object summaries through `response_attr`
- `list` requiring context like bucket or rule

List should return model instances whenever service contract plausibly allows it.

Load `../botocraft-service-authoring/references/common-manager-patterns.md`
when choosing a concrete `get` or `list` pattern.

## Create/update/delete heuristics

- `create`: model instance as main parameter; extra keyword args only when AWS
  API genuinely needs them
- `update`: use operation that naturally updates existing object, not recreate
- `delete`: prefer single direct delete when AWS supports it

Escalate to advanced manager skill for deactivate-then-delete or decorator-heavy
flows.

## Generic methods

Add non-CRUD methods only when they provide real ergonomic value and clearly map
to resource identity or lifecycle.

## Output

Manager authoring result should name:

- manager contract type
- chosen boto3 methods
- required arg renames/overrides
- return-shape strategy
- which methods remain intentionally absent
