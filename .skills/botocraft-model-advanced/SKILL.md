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

When discovering or adding `relations:`, use a two-stage workflow:

1. suggest candidate relations and stop for keep/drop review
2. implement only approved candidates

Do not skip the review stage for fuzzy or doc-assisted relation guesses unless
the user explicitly asks for a direct implementation pass.

Load `../botocraft-service-authoring/references/relations-properties-bespoke.md`
for concrete patterns.
Load `../botocraft-service-authoring/references/relation-discovery.md` when you
need the detailed relation-suggestion workflow.

## Relation discovery workflow

For relation-heavy authoring:

- start from primary-model fields and nested shapes
- look for likely foreign identifiers such as `*Id`, `*Ids`, `*Arn`,
  `*Arns`, `*Name`, and `*Names`
- exclude the model's own `primary_key`, `arn_key`, and `name_key`
- map candidate stems to botocore model names first, then to Botocraft public
  model names
- only propose relations to primary models
- use AWS docs for fuzzy cases that suffix matching misses

Stage 1 output should present candidate relations with:

- source model and field path
- proposed relation name
- target primary model
- likely transformer shape
- singular vs `many`
- confidence and evidence

Stage 2 should:

- implement only approved relations
- prefer mapping transformers first
- use regex only for stable structured extraction
- keep rejected or unclear candidates as raw identifiers or properties

If there is no stable lookup path to another primary model, do not force a
relation.

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
