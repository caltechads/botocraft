---
name: botocraft-model-advanced
description: Handle advanced Botocraft model authoring cases such as `alternate_name`, cross-service collisions, field/type-name conflicts, properties, relations, composite `pk` values, bespoke models, and EC2-style secondary-model cleanup. Use this whenever common `models.yml` authoring is not enough or when the user asks how to model tricky relationships, collisions, derived identifiers, or shape mismatches in Botocraft.
---

# Botocraft Model Advanced

Use this skill only after common model authoring reveals real complexity.

## Collision rules

Check cross-service public names before finalizing models.
Use `alternate_name` when:

- primary model name already exists in another service
- secondary model collides with common cross-service type
- field name and inferred type name would become confusing or broken

Prefer smallest rename that keeps public API understandable.

Load `../botocraft-service-authoring/references/model-collision-and-tags.md`
for established rename patterns.

## Properties vs relations vs mixins

Use property when derived value comes from local fields and small YAML
transformer is enough.

Use relation when:

- target is another primary model
- stable lookup path exists
- result should feel object-like to callers

Prefer mapping transformers first. Use regex only when structure is stable and
mapping cannot express it cleanly.

Use model mixin only when behavior needs real Python logic or several calls.

Load `../botocraft-service-authoring/references/relations-properties-bespoke.md`
for concrete patterns.

## Bespoke model rule

Reach for `bespoke: true` only when user-facing resource is real but AWS does
not expose one clean shape that maps to it.

Before choosing bespoke, rule out:

- shape-backed model plus field overrides
- `output_shape`
- extra fields on otherwise normal model
- manager decorator or mixin

## Composite identity

Use property-based `pk` only when resource identity truly spans multiple
fields and manager methods naturally accept that composite form.

## EC2-grade cleanup

EC2 is reference for:

- `Image -> AMI`
- secondary rename storms
- relation-rich models
- composite derived values

Load `../botocraft-service-authoring/references/ec2-case-study.md` when task
looks similarly dense.

## Output

Advanced model result should explain:

- why simple shape-backed model was not enough
- exact collision or relation rule chosen
- why property, relation, mixin, or bespoke was appropriate
