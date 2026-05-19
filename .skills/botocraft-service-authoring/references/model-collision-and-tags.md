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

## Tag shape guidance

Most services keep tag field as list-like tag models or dict-like structures
already established by repo conventions.

EC2 special rule:

- field name must still be `Tags`
- tag conversion for create/update often happens in manager mixin because EC2
  wants `TagSpecifications`

Do not invent a new Botocraft-side tag field name.
