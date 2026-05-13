---
name: botocraft-service-discovery
description: Discover the right first slice of a Botocraft AWS service by identifying the botocore alias, likely primary models, readonly versus CRUDL contract, manager naming, and operation inventory before YAML authoring starts. Use this whenever Botocraft service authoring is still in discovery mode, when the user asks what resources to model first, how to classify resources, what the first safe scope is, or which boto3 operations should drive Botocraft managers.
---

# Botocraft Service Discovery

Use this skill before YAML edits when service scope still fuzzy.

## Inspect first

Use repo runbook and botocore inspection to answer:

- correct botocore alias
- likely primary models
- which shapes are only helpers
- readonly vs create-only vs full CRUDL candidates
- which operations already imply manager names and method surface
- whether first pass should start with one or two models only

Start with:

- `botocraft botocore services`
- `botocraft botocore models <service>`
- `botocraft botocore primary-models <service>`
- `botocraft botocore model <service> <shape> --dependencies --operations`

## Primary-model detection

Treat model as likely primary when most are true:

- represents real AWS resource, not wrapper/helper structure
- has stable identity field usable as `primary_key`
- has at least one credible `get` or `list` path
- has understandable request and response shapes
- could plausibly own a manager users would call directly

Deprioritize shapes that are:

- response envelopes
- nested members reused across resources
- config fragments that never stand alone
- exceptions or pagination wrappers

## Contract classification

Classify each candidate early:

- readonly: only read/list style operations, or writes too unnatural to expose
- writable not updatable: supports `create`, `get`, `list`, maybe `delete`
- fully modifiable: supports `create`, `get`, `list`, `update`, `delete`

Default to narrower public contract when AWS surface is irregular.

## Manager naming

Manager name should follow chosen primary model name exactly.
If public model name needs `alternate_name`, manager follows public name, not raw
botocore shape name.

## First safe slice

Prefer one or two primary models with:

- clear identity
- low ambiguity on readonly vs writable
- credible `get` and `list`
- limited collision risk
- minimal need for bespoke assembly

Delay edge-case models until first sync looks healthy.

## Escalate when needed

Load `../botocraft-model-advanced/SKILL.md` if you see:

- cross-service naming collisions
- composite keys
- likely bespoke model
- heavy relation/property questions

Load `../botocraft-manager-advanced/SKILL.md` if you see:

- identifier-only list ops
- describe wrappers that need decorators
- context-required get/list
- multi-call lifecycle workflows

## Output

Discovery result should hand off:

- botocore alias
- first primary models
- contract classification per model
- candidate identity fields
- likely boto3 ops for `get`, `list`, `create`, `update`, `delete`
- specific reasons an advanced leaf is or is not needed
