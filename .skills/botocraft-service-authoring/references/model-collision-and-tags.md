# Model Collisions And Tags

## Collision categories

Repo already has repeated public or raw shape names:

- primary: `Image`, `Parameter`, `Rule`, `User`, `DBInstance`, `DBSubnetGroup`
- secondary: `Endpoint`, `Resource`, `Tag`, `Condition`, `Instance`, many more

Collisions are normal. Plan for them early.

## `alternate_name`

Use `alternate_name` when public Python class name would otherwise collide or
be confusing.

Established examples:

- `ec2.Image -> AMI`
- `bedrock.FoundationModelSummary -> FoundationModel`
- `docdb.DBInstance -> DocDBInstance`
- `s3.Object -> S3Object`
- `ecs.Tag -> ECSTag`

Prefer names that preserve domain meaning, not arbitrary suffixes.

## Field/type-name collisions

Watch for cases where field name and inferred type name match and generator
would create awkward or broken annotations. Typical fixes:

- rename secondary model with `alternate_name`
- rename field when public Botocraft surface benefits
- override field `python_type` when name is correct but type inference is not

Secondary models are most collision-prone. Keep overrides small and targeted.

When collision is triggered by a **manager `response_attr`** or return type
inference (not just a public rename), see also
`generator-yaml-pitfalls.md` (`alternate_name` on secondary shapes).

## Create-result nested renames

When a create operation returns a nested resource whose shape name matches the
primary model, rename under the create result in `models.yml`:

```yaml
CreateNatGatewayResult:
  fields:
    NatGateway:
      rename: NatGatewayInstance
```

Load `generator-yaml-pitfalls.md` for the full table and EC2 examples.

## Tag normalization

Botocraft-side field must end up named `Tags`.

Raw AWS sources seen in repo:

- `Tags`
- `tags`
- `TagList`

Normal patterns:

```yaml
fields:
  tags:
    rename: Tags
```

```yaml
fields:
  TagList:
    rename: Tags
```

If AWS already exposes `Tags`, keep it.
If the model already has tags as an attribute but under another name, such as
`tags` or `TagList`, rename that field to `Tags`.

Do not leave tag-bearing primary-model fields under near-miss names just because
AWS used them.

## Tag shape guidance

For primary models, Botocraft should expose tags through the normal tag system,
centered on a field named exactly `Tags`.

Preferred order:

1. keep native `Tags` when AWS already provides it
2. rename any existing tag-bearing field to `Tags`
3. add `extra_fields.Tags` when tags belong on the primary model but come from a
   follow-up API rather than the main shape
4. use decorators to hydrate missing tags on `get`, `list`, or `create` when
   one generated call plus enrichment is enough
5. use manager mixins only when tag handling needs translation or
   reconciliation across multiple calls

Most services keep the `Tags` field as list-like tag models or dict-like
structures already established by repo conventions.

Normal Botocraft public contract is the model field `Tags` plus the tag system
around `.tags`. Do not make bespoke per-primary `get_tags`, `put_tags`, or
`delete_tags` helpers the main user-facing tag API.

EC2 special rule:

- field name must still be `Tags`
- tag conversion for create/update often happens in manager mixin because EC2
  wants `TagSpecifications`
- this is translation inside the Botocraft tag system, not a reason to switch
  back to bespoke tag helper methods

Do not invent a new Botocraft-side tag field name.
