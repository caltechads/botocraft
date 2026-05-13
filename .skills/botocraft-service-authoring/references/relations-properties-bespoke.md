# Relations, Properties, And Bespoke Models

## Property vs relation

Use property when value is derived from current model fields and no extra lookup
should happen.

Good property cases:

- composite `pk`
- parsed cluster name from ARN
- parsed repository name or tag fragment
- small booleans derived from existing fields

Use relation when user should naturally get another primary model and stable
lookup path exists.

Good relation cases:

- subnet -> VPC
- service -> cluster
- instance -> AMI

## Transformer preference

Prefer mapping transformer first.
Use regex only when mapping cannot express stable extraction cleanly.

Regex is acceptable for:

- ARN fragment extraction
- structured group/name parsing

Do not reach for regex when direct field mapping already works.

## Mixins

Use model mixin when:

- behavior depends on several fields
- convenience behavior belongs on object
- YAML transformer would become contorted

## Bespoke model rule

Use `bespoke: true` only when user-facing resource is real but AWS does not
offer one clean core shape.

Repo examples:

- `s3.Bucket`
- `sqs.Queue`
- `inspector2.FindingsReport`

Try these before bespoke:

- shape-backed model plus `fields`
- `output_shape`
- `extra_fields`
- decorator or manager mixin

## Composite `pk`

Property-based composite identity is appropriate when manager methods naturally
need multiple values together and repo examples already show ergonomic pattern.

Examples:

- ECS service `pk`
- S3 object `pk`
- Application Auto Scaling composite keys
