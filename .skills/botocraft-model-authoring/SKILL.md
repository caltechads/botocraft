---
name: botocraft-model-authoring
description: Author Botocraft `models.yml` for primary and supporting models by choosing `primary_key`, `arn_key`, `name_key`, `input_shapes`, `output_shape`, field overrides, writable inference, and tag normalization. Use this whenever the user is working on Botocraft model definitions, asking how to build the base model shape, how to detect primary model fields, or how to normalize AWS fields into stable Botocraft model interfaces.
---

# Botocraft Model Authoring

Use this skill for common-path `models.yml` work.
If primary model still uncertain, load `../botocraft-service-discovery/SKILL.md`
first and come back with a narrow candidate set.

## Base recipe

For each primary model, decide in this order:

1. public model name
2. `primary_key`
3. `arn_key` if present
4. `name_key` if present
5. `input_shapes`
6. `output_shape` only when response adds useful fields
7. targeted `fields` overrides
8. minimal secondary-model overrides actually needed

## Writability inference

Default to `input_shapes` as main source of truth.
Prefer inferred readonly behavior over manual field-by-field overrides.
Use explicit `readonly` only when inference is wrong or public contract is
intentionally narrower.

## Primary-model field guidance

- `primary_key`: stable unique identifier users can pass back to manager `get`
- `arn_key`: add when ARN exists and is useful for relations or lookup
- `name_key`: add when human-friendly name is stable and meaningful
- `output_shape`: add when describe/list response enriches base shape

## Tags rule

Botocraft-side tag field must end up named `Tags`.
If AWS shape already uses `Tags`, keep it.
If the model already has tags under another attribute such as `tags` or
`TagList`, rename that field to `Tags`.
If tags belong on the primary model but come from a follow-up API instead of the
main shape, add them as `extra_fields.Tags`.
Primary models should expose tags through the Botocraft tag system on `Tags`,
not through bespoke `get_tags`, `put_tags`, or `delete_tags` helper methods.
Prefer list-of-dict/tag-model representation that existing repo patterns use.

Load `../botocraft-service-authoring/references/model-collision-and-tags.md`
when tag shape or naming gets tricky.

When a manager `response_attr` names a shape that collides with a primary model
or field type (e.g. `VolumeModification`), load
`../botocraft-service-authoring/references/generator-yaml-pitfalls.md` for
`alternate_name` and create-result `*Instance` rename patterns.

## Secondary models

Only define secondary models explicitly when it materially improves generation:

- `alternate_name`
- field overrides
- `force_create`
- mixin/property needs
- collision avoidance

Do not declare every nested shape by default.

## Escalate when needed

Load `../botocraft-model-advanced/SKILL.md` for:

- properties
- relations
- bespoke models
- `alternate_name`
- field/type-name collisions
- composite `pk`

## Output

Model authoring result should name:

- primary models chosen
- identity fields
- `input_shapes` and `output_shape`
- tag normalization decisions
- secondary models that need explicit config
