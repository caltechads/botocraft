---
name: botocraft-manager-authoring
description: Author Botocraft `managers.yml` for core manager contracts by choosing readonly versus writable manager shape, implementing `get`, `list`, `create`, `update`, `partial_update`, `delete`, and `get_many`, and ensuring methods return Botocraft model instances instead of raw AWS payloads. Use whenever the user designs Botocraft managers, maps boto3 operations to manager methods, or adds non-CRUD helpers (attach, associate, routes, egress) — including generator pitfalls for empty outputs, `Return`, and `response_attr`.
---

# Botocraft Manager Authoring

Use this skill for common-path `managers.yml` work.

## Manager naming

The `managers.yml` key must use the botocore shape name from `models.yml`, not
the public `alternate_name`.

Example:

```yaml
# models.yml
primary:
  DomainStatus:
    alternate_name: OpenSearchDomain

# managers.yml
DomainStatus:
  methods:
    get:
      boto3_name: describe_domain
```

Generated manager classes still follow the public model name
(`OpenSearchDomainManager` in this example), but the YAML key must stay on the
raw botocore shape name so generation can attach the manager to the correct
primary model.

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

## Generator pitfalls (`return_type` / `response_attr`)

Before adding attach/detach, route mutations, associate/disassociate, or any
helper whose boto output is not a plain describe/list payload, load
`../botocraft-service-authoring/references/generator-yaml-pitfalls.md`.

In short:

- **`Return` in output** → `return_type: bool | None` and `response_attr: Return`
- **Empty boto output** → `return_type: None` only (never `response_attr: Return`)
- **Top-level resource shape** (e.g. `AttachVolume` → `VolumeAttachment`) →
  `response_attr: None`
- **Nested resource field** (e.g. `VolumeModification` on modify) →
  `response_attr: <field name>`

After sync, inspect the generated method body in `botocraft/services/` for
invalid `response = ...` assignment (see reference checklist).

## Output

Manager authoring result should name:

- manager contract type
- chosen boto3 methods
- required arg renames/overrides
- return-shape strategy
- which methods remain intentionally absent
