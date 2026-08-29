# Generator YAML Pitfalls

Repo lessons from EC2 service expansion (phases 2–4) and Bedrock AgentCore
service authoring. Use this when adding non-CRUD manager methods or secondary
models, then **inspect generated code** in `botocraft/services/<service>.py`
before calling the slice done.

## Quick reference

| Situation | Safe YAML pattern |
|-----------|-------------------|
| Operation output has `Return` (e.g. `CreateRoute`) | `return_type: bool \| None`, `response_attr: Return` |
| Operation output is **empty** (e.g. `DeleteRoute`, `DisassociateRouteTable`, `detach_internet_gateway`) | `return_type: None` — **do not** use `response_attr: Return` |
| Top-level output shape **is** the resource (e.g. `AttachVolume` → `VolumeAttachment`) | `response_attr: None` (generator wraps full boto dict in that shape) |
| Nested output field is the resource (e.g. `ModifyVolume` → `VolumeModification`) | `response_attr: VolumeModification` (or renamed field) — not `None` |
| Field type name equals a generated model name (e.g. `VolumeModification` on `Volume`) | `alternate_name: EC2VolumeModification` under `secondary` in `models.yml` |
| Create response nested resource name collision | `Create*Result.fields.<Model>.rename: <Model>Instance` in `models.yml` |
| `botocraft botocore model <service> <Shape>` (or `--dependencies`/`--operations`) raises `RecursionError` for a shape whose fields look ordinary | See "RecursionError workarounds" below |
| `botocraft sync` raises `ValueError: Model <Name> already defined in "botocraft.services.<other_service>"` | Model names are global across **all** services — `alternate_name` (primary) or `secondary: <Name>: {alternate_name: ...}` (nested) even with zero local naming conflict |
| Field name equals its own field-type name (e.g. `WarmUpConfiguration` field of type `WarmUpConfiguration`) | `fields: <field>: {rename: <Something>}` — pydantic can't resolve a forward ref that shadows itself |
| Field literally named `arn` or `name` on a primary model | `fields: {arn: {rename: Arn}}` / `{name: {rename: <somethingName>}}` — both shadow `PrimaryBoto3Model.arn`/`.name` properties and fail `TestBedrockShadowedFieldAliases`-style guard tests |
| Field literally named `schema` (on any model, not just primary) | `fields: {schema: {rename: schemaDefinition}}` — shadows a `Boto3Model`/pydantic `BaseModel.schema` attribute |
| Field named after a Python keyword (`lambda`, `class`, …) | `fields: <field>: {rename: <naturalName>}` — pick a name that describes what it holds (e.g. `lambda` holding a `LambdaTransformConfiguration` → `lambdaConfiguration`, not `lambda_`) |
| A resource's only "create"/"update" boto3 operation is a **batch** call (`batch_create_x`, `batch_update_x`) taking a list | Don't use the reserved `create`/`update` method keys — they always prepend `model: "<ModelName>"` as the first parameter, which doesn't fit a list-of-items call. Use a custom method name (`batch_create`/`batch_update`, matching the `batch_delete` precedent on bedrock's `AccessKey` manager); pass the list straight through and return the raw `Batch*Output` (`return_type`, `response_attr: None`) rather than faking a single-model return, since a batch call can partially fail |
| Custom (non-CRUD) manager method's `return_type` names a shape ruff reports as `F821 Undefined name` | The reserved CRUD method types (`get`/`list`/`create`/`update`/`delete`) auto-walk their response shape into the dependency graph; custom method names don't. Declare the shape explicitly under `secondary: <ShapeName>: {}` so the class actually gets generated, **and** quote the return type as a literal Python string so it's a forward reference: `return_type: '"BatchCreateXOutput"'` (note the nested quotes — a bare `return_type: "BatchCreateXOutput"` emits an *unquoted* annotation in the generated code, which can `F821` if the class is defined later in the file) |

## RecursionError workarounds

Several different failure shapes all surface as `RecursionError`, and they
need different fixes. Don't reach for `alternate_name` blindly — diagnose
first with the shape-walker script below, which tells you in one shot whether
you have a genuine data cycle and exactly which field causes it.

### 1. Global model-name collision (fixed with `alternate_name`)

Botocraft model names are unique across the **whole SDK** (see "Global
model-name collisions" below) — this isn't recursion at all, but a second,
unrelated shape reusing a name your service also uses can produce confusing
`RecursionError`-adjacent behavior in ad-hoc inspection tools. The fix from
`botocraft/data/ecs/models.yml` — used for both primary and secondary models
— is to give the offending shape an `alternate_name`:

```yaml
secondary:
  Resource:
    alternate_name: AgentCoreServiceResource
```

### 2. Genuine cycle deep in a nested field (fixed by cutting one field to opaque `dict`)

Some AWS shapes are **actually** self-referential — most often JSON-Schema-
style "describe an arbitrary tool's parameters" shapes, which naturally
recurse (`SchemaDefinition.properties` is a map of `SchemaDefinition`,
`SchemaDefinition.items` is a `SchemaDefinition`). Don't assume `alternate_name`
fixes this — it doesn't; the shape really does contain itself, and pydantic
would need a real forward-referencing recursive model, which botocraft's
generator doesn't support.

**Diagnose with a real shape walk** (bypasses the debug CLI's own
recursion-unsafe printer entirely — see `botocraft/cli/botocore.py`'s
`render_structure`, which has zero cycle detection and will `RecursionError`
on both real cycles and merely-deep trees):

```python
import botocore.session
session = botocore.session.get_session()
sm = session.get_service_model("<service>")

def walk(shape, path):
    if shape.name in path:
        print("CYCLE:", " -> ".join(path + [shape.name]))
        return True
    path = path + [shape.name]
    if len(path) > 60:
        print("TOO DEEP (not a short cycle):", " -> ".join(path))
        return True
    if shape.type_name == "structure":
        return any(walk(m, path) for m in shape.members.values())
    if shape.type_name == "list":
        return walk(shape.member, path)
    if shape.type_name == "map":
        return walk(shape.value, path)
    return False

walk(sm.shape_for("CreateGatewayTargetRequest"), [])
# CYCLE: CreateGatewayTargetRequest -> TargetConfiguration -> McpTargetConfiguration
#        -> McpLambdaTargetConfiguration -> ToolSchema -> ToolDefinitions
#        -> ToolDefinition -> SchemaDefinition -> SchemaProperties -> SchemaDefinition
```

The cycle names the exact repeating shape (`SchemaDefinition`) and the field
one level up that references it (`ToolDefinition.inputSchema`/`outputSchema`).
Cut it there — override just those two fields as opaque JSON, rather than the
whole shape family:

```yaml
secondary:
  ToolDefinition:
    fields:
      inputSchema:
        python_type: "dict[str, Any] | None"
        imports:
          - from typing import Any
      outputSchema:
        python_type: "dict[str, Any] | None"
        imports:
          - from typing import Any
```

Re-run the walk script (with `SchemaDefinition` treated as a leaf) against
every operation shape that uses the resource (`Create*Request/Response`,
`Update*Request/Response`, `Get*Response`, the base shape itself) to confirm
there's no *second* cycle before writing YAML.

If after cutting the cycle the base resource shape (e.g. `GatewayTarget`) is
now clean and richer than the list-item shape (e.g. `TargetSummary`), key the
primary model on the list-item shape with the base shape merged in via
`output_shape` — same pattern as any other summary-vs-detail resource pair —
rather than leaving the resource only partially modeled. Watch for a second
gotcha here: if the base shape's public name is the same as what you want the
*primary model's* `alternate_name` to be (e.g. base shape literally named
`GatewayTarget`, and you want the primary model's public class to also be
`GatewayTarget`), alias the base shape too or you'll get two classes with the
same name (see "Global model-name collisions" below — this is a same-service,
not cross-service, instance of it):

```yaml
primary:
  TargetSummary:
    alternate_name: GatewayTarget
    output_shape: GatewayTarget   # the raw botocore shape name
secondary:
  GatewayTarget:                  # alias the raw shape so it doesn't collide
    alternate_name: GatewayTargetDetail
    # with the primary model's own public name above
```

### 3. Real self-wrap recursion (fixed by removing `output_shape`)

If `Get<X>Output` (or `Create/Update<X>Output`) has **no fields of its own**
beyond wrapping the base shape itself — e.g. `GetEventOutput` is just
`{event: Event}` — do **not** set it as `output_shape` on the `Event` primary
model. Merging `output_shape` fields into a model named the same as the
wrapped field makes the generator try to embed `Event` inside itself forever.

**Symptom:** `RecursionError: maximum recursion depth exceeded`, and a traced
call stack (see below) shows the *exact same shape name* repeating every few
frames (`Event → PayloadType → ... → Event → PayloadType → ...`), not a
genuinely different shape each time.

**Fix:** drop `output_shape` for that model; keep the manager's `get`/`create`
methods unwrapping via `response_attr: event` (the nested field name) instead.

### 4. Genuinely opaque/empty `document`-typed shapes

AWS `document` shapes (arbitrary JSON) sometimes show up as structures with
"No members" (e.g. `MemoryDocument`). These are *not* the cause of recursion by
themselves — an empty structure formats fine. Don't add defensive
`python_type` overrides for these unless a real error names them; verify with
the tracing technique below before "fixing" a non-problem.

### Diagnosing which kind you have

Reproduce inside a Python shell rather than guessing from the traceback alone.
`uv run botocraft shell` (or `python -c "from botocraft.services import *"`)
is the fastest way to get a live import to poke at; for recursion specifically,
monkeypatch the converter to print the shape name at each call so you can see
whether the same shape repeats (real self-wrap) or the stack is just very deep
across many distinct shapes (rare, likely a different bug):

```python
import sys
sys.setrecursionlimit(300)
import botocraft.sync.shapes as shapes

orig = shapes.StructureShapeConverter.to_python
depth = [0]
def traced(self, shape, quote=True, name_only=False):
    depth[0] += 1
    print("  " * min(depth[0], 60) + str(getattr(shape, "name", shape)))
    try:
        return orig(self, shape, quote=quote, name_only=name_only)
    finally:
        depth[0] -= 1
shapes.StructureShapeConverter.to_python = traced

from botocraft.cli import cli
sys.argv = ["botocraft", "sync", "--service", "<service>"]
try:
    cli(obj={})
except RecursionError:
    print("RECURSION HIT")
```

A repeating exact shape name (e.g. `Event` every N frames, always the model
you're currently authoring) means case 3 (self-wrap via `output_shape`) — fix
by dropping `output_shape`. If the trace instead shows a chain of genuinely
different shape names before erroring, use the direct `botocore.model` shape
walk from case 2 to name the exact cyclic field and cut it there. Prefer the
case-2 walk as the first diagnostic step — it's faster and gives you the exact
field, whereas the traced `StructureShapeConverter` run only tells you *that*
the real sync pipeline (not just the debug CLI) hits the same wall.

## Global model-name collisions

Botocraft model names are unique **across the whole SDK**, not just within one
service — `botocraft sync` (unscoped) registers every generated model into one
global namespace and raises `ValueError: Model <Name> already defined in
"botocraft.services.<other>"` on the second definition. Generic AWS shape
names (`Resource`, `Action`, `Certificate`, `Policy`, `CreatePolicyResponse`,
...) collide often when a new service reuses common nouns already used by
`ecs`, `ecr`, `elbv2`, `inspector2`, etc.

- `--service <name>`-scoped sync will **not** catch these — the collision only
  surfaces during an unscoped `botocraft sync` once model registration spans
  services. Always run a full `botocraft sync` before calling authoring done,
  per the service-verification skill, specifically to catch this class of bug.
- Fix with `alternate_name` on the colliding shape (primary or `secondary:`),
  prefixed with something service-specific (`AgentCorePolicyGenerationResource`,
  `CodeInterpreterCertificate`, `GatewayRuleAction`, `CreateAgentCorePolicyResponse`).
- A scoped `--service` sync run also has a side effect worth knowing:
  `purge_docs()` deletes **all** service `.rst` docs before regenerating only
  the scoped service, silently breaking every other service's docs. If you've
  been iterating with `--service` while chasing errors, finish with one clean
  unscoped `botocraft sync` to restore the doc tree before finishing up.

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
