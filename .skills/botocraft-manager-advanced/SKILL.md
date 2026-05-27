---
name: botocraft-manager-advanced
description: Solve advanced Botocraft manager cases such as decorators, manager mixins, identifier-to-model conversion, context-required list/get flows, two-step disable/delete behavior, irregular non-CRUD methods, and higher-level workflows inferred from boto3 operation shapes. Use whenever common `managers.yml` is insufficient, AWS returns wrappers or empty outputs, or you need safe `return_type`/`response_attr` for attach/route/associate-style helpers — load generator-yaml-pitfalls before syncing.
---

# Botocraft Manager Advanced

Use this skill only when common manager patterns stop being enough.

## Decorator vs mixin

Prefer decorator when generated call is basically correct and only needs:

- wrapper/result unboxing
- identifier list -> model instances
- lightweight post-processing
- missing-result normalization
- batched follow-up lookups around AWS per-call limits
- tag hydration onto model field `Tags`

Prefer manager mixin when method needs:

- multiple AWS calls
- custom control flow
- richer lifecycle workflow
- behavior too irregular for generated method ergonomics

## Advanced `get` and `list`

Reach here for cases like:

- `describe_instances` returning Reservations that must become Instances
- list operations returning ARNs or IDs that must become models
- context-required list/get like S3 objects needing `Bucket` or EventBridge
  targets needing `Rule`
- read methods that need tag-enrichment follow-up calls

For primary-model tags, enrichment should populate the Botocraft model field
named exactly `Tags`. If the source attribute was `tags` or `TagList`, rename it
to `Tags` in the model contract first. Do not default to bespoke `get_tags`,
`put_tags`, or `delete_tags` helpers.

Load `../botocraft-service-authoring/references/common-manager-patterns.md`
for concrete examples.

## Two-step lifecycle methods

Model delete workflow honestly.
If AWS requires disable/deregister/deactivate before delete:

- expose explicit intermediate lifecycle method when useful
- do not fake single-step delete if semantics matter
- consider model shortcut method when flow is instance-scoped

## Generator pitfalls for irregular methods

Lifecycle helpers (routes, attach/detach, associate/disassociate, authorize/revoke
egress) often have empty outputs, top-level resource outputs, or `Return` flags.

Load `../botocraft-service-authoring/references/generator-yaml-pitfalls.md`
**before** writing YAML. Validate with botocore `operation_model`, then inspect
generated code after sync. Escalate to mixin only when YAML cannot express the
return shape safely.

## Generic method discovery

Scan operation input shapes for methods that accept resource identity:

- ARN
- name
- ID
- composite key already modeled on object

Add helpers only when they are naturally scoped to resource and not merely
obscure boto3 surface area.

## Mixin gap detection

Good mixin candidates repeat one of these patterns:

- same follow-up enrichment across several methods
- same conversion logic across services or models
- multi-call workflow user will reasonably want more than once

Tag-specific mixin cases are things like EC2 `TagSpecifications` conversion or
update-time reconciliation of model `Tags`, not replacing the Botocraft tag
system with separate tag helper methods.

## EC2/ECS reference

Load `../botocraft-service-authoring/references/ec2-case-study.md` when task
looks like EC2 Reservations, ECS identifier lists, or rich lifecycle helpers.

## Output

Advanced manager result should explain:

- why common manager pattern failed
- why decorator or mixin was right
- how model-instance return contract is preserved
