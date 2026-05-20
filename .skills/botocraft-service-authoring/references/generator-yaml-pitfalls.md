# Generator YAML Pitfalls

Repo lessons from EC2 service expansion (phases 2–4). Use this when adding
non-CRUD manager methods or secondary models, then **inspect generated code**
in `botocraft/services/<service>.py` before calling the slice done.

## Quick reference

| Situation | Safe YAML pattern |
|-----------|-------------------|
| Operation output has `Return` (e.g. `CreateRoute`) | `return_type: bool \| None`, `response_attr: Return` |
| Operation output is **empty** (e.g. `DeleteRoute`, `DisassociateRouteTable`, `detach_internet_gateway`) | `return_type: None` — **do not** use `response_attr: Return` |
| Top-level output shape **is** the resource (e.g. `AttachVolume` → `VolumeAttachment`) | `response_attr: None` (generator wraps full boto dict in that shape) |
| Nested output field is the resource (e.g. `ModifyVolume` → `VolumeModification`) | `response_attr: VolumeModification` (or renamed field) — not `None` |
| Field type name equals a generated model name (e.g. `VolumeModification` on `Volume`) | `alternate_name: EC2VolumeModification` under `secondary` in `models.yml` |
| Create response nested resource name collision | `Create*Result.fields.<Model>.rename: <Model>Instance` in `models.yml` |

## Why these matter

### Empty output vs `Return`

If boto returns `{}` but YAML sets `response_attr: Return`, sync may generate
broken code such as `response = None(**_response)` or attribute access on a
wrapper that has no `Return` member.

**Symptom in generated code:** constructing a result type from `None`, or
reading `.Return` when the operation output has no members.

**Fix:** `return_type: None` and omit misleading `response_attr`.

### `Return` present

When output shape includes `Return` (boolean success flag), mirror ingress-style
patterns already used on EC2 security groups and routes:

```yaml
create_route:
  boto3_name: create_route
  return_type: bool | None
  response_attr: Return
```

### Top-level resource output (`response_attr: None`)

Some operations use the resource shape as the **root** output shape, not nested
under a `*Result` key. Example: `AttachVolume` output shape name is
`VolumeAttachment`; boto response keys are `VolumeId`, `InstanceId`, `Device`, …
at the top level.

**Safe pattern:**

```yaml
attach:
  boto3_name: attach_volume
  response_attr: None
```

Generated code should look like `response = VolumeAttachment(**_response)`, not
`response = AttachVolumeResult(**_response).VolumeAttachment` unless the API
actually nests the resource.

Do not confuse with empty output: empty means no fields at all; top-level
resource means the dict **is** the attachment object.

### Secondary `alternate_name` (Pydantic collision)

When a field's inferred type name matches an existing model class name, sync
can fail at generation time with a Pydantic collision error.

**Example:** `VolumeModification` field on `Volume` vs `VolumeModification`
secondary shape → add:

```yaml
secondary:
  VolumeModification:
    alternate_name: EC2VolumeModification
```

Prefer service-prefixed public names (`EC2*`, `DocDB*`, `S3*`) consistent with
existing repo style.

### Create-result nested rename

When create returns a nested structure whose shape name collides with the
primary model, rename in `models.yml` under the create result fields:

```yaml
CreateRouteTableResult:
  fields:
    RouteTable:
      rename: RouteTableInstance
```

Same pattern as `NatGatewayInstance`, `VpcPeeringConnectionInstance`, etc. on EC2.

## Validate before YAML

Inspect the operation with botocore (API names are **PascalCase** in
`operation_model`, boto3 client methods are snake_case):

    .venv/bin/python -c "
    import boto3
    c = boto3.client('ec2', region_name='us-east-1')
    op = c._service_model.operation_model('AttachVolume')
    print('in required:', list(op.input_shape.required_members))
    print('in members:', list(op.input_shape.members.keys()))
    out = op.output_shape
    print('output shape:', out.name if out else None)
    print('out members:', list(out.members.keys()) if out and out.members else 'EMPTY')
    "

Decision guide from inspection:

- `out members: EMPTY` → `return_type: None`
- `'Return' in out.members` and you only need success flag → `return_type: bool | None`, `response_attr: Return`
- `out.name` matches a known resource shape and members are resource fields → `response_attr: None` if those keys are at top level of boto response
- single nested member whose name matches resource → `response_attr: ThatMemberName`

## Post-regen inspection (required)

After `botocraft sync`, open the new manager method in
`botocraft/services/<service>.py` and confirm:

1. No `None(**_response)` or similar invalid construction.
2. Empty-output methods do not assign `response = SomeResult(**_response)` when
   boto returns `{}`.
3. Return type matches what the method actually returns (bool, model, or void).
4. `attach`/`detach`/`associate` helpers pass through required boto args
   (`RouteTableId`, `VolumeId`, etc.) from `managers.yml` `args:` blocks.

## EC2 examples (verified)

| Method | Pattern |
|--------|---------|
| `RouteTableManager.create_route` | `return_type: bool \| None`, `response_attr: Return` |
| `RouteTableManager.delete_route` / `replace_route` | `return_type: None` |
| `RouteTableManager.disassociate` | `return_type: None` |
| `RouteTableManager.associate` | `response_attr: None` → `AssociateRouteTableResult` |
| `VolumeManager.attach` / `detach` | `response_attr: None` → `VolumeAttachment` |
| `VolumeManager.update` | `response_attr: VolumeModification` + `EC2VolumeModification` alias |
| `VolumeManager.create` | `response_attr: None` → top-level `Volume` (supports `SnapshotId` via model) |
| `InternetGatewayManager.attach` | `return_type: None` |
| `EC2VpcEndpointManager.delete` | `return_type: "DeleteVpcEndpointsResult"`, `response_attr: None` |
| `FlowLogManager.delete` | same pattern for `DeleteFlowLogsResult` |
| `InstanceManager.modify_*` | one YAML method per attribute, all `boto3_name: modify_instance_attribute`, `return_type: None`; pass `AttributeValue` / `AttributeBooleanValue` / `BlobAttributeValue` wrappers |
| `NatGatewayManager.associate_address` | `response_attr: None` → `AssociateNatGatewayAddressResult` |
| `VpnConnectionManager.modify` | `response_attr: VpnConnectionInstance` after `ModifyVpnConnectionResult` field rename in `models.yml` |

### `modify_instance_attribute` (scoped helpers)

Boto exposes one operation with many optional attribute members. Add **separate**
YAML methods per attribute (do not expose one mega-method in a single phase):

```yaml
modify_instance_type:
  boto3_name: modify_instance_attribute
  return_type: None
  args:
    InstanceId:
      required: true
    InstanceType:
      required: true
    DryRun:
      default: "False"
```

Generated methods still include other operation members as optional keyword args
(generator merges the shared operation shape). Callers should pass only the
attribute being changed plus `InstanceId`.

### Nested result field rename (`ModifyVpnConnectionResult`)

When `response_attr` points at a nested resource whose shape name matches a
primary model, add a create-result-style rename under `models.yml`:

```yaml
ModifyVpnConnectionResult:
  fields:
    VpnConnection:
      rename: VpnConnectionInstance
```

Then set `response_attr: VpnConnectionInstance` on the manager method.
