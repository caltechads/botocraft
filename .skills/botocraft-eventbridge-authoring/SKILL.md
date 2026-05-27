---
name: botocraft-eventbridge-authoring
description: Author Botocraft EventBridge support for AWS services, whether schemas come from AWS Schema Registry or must be built from AWS documentation examples. Use this whenever the user wants to add or expand botocraft.eventbridge support, add all EventBridge events for a service, export-service for a whole service, export EventBridge schemas, wire EventFactory mappings, or implement any mix of native service events plus AWS API Call via CloudTrail (detail-type AWS API Call via CloudTrail on aws.<service>). Use even when the user does not name CloudTrail—if export-service or service docs include that detail-type, apply the CloudTrail branch in this skill for that event only. Also use for CloudTrail detail payloads, requestParameters, parsed_request, CloudTrailApiCallMixin, or lazy botocore-backed typing.
---

# Botocraft EventBridge Authoring

Use this skill when task is specifically about Botocraft EventBridge support.
Keep raw-model acquisition, wrapper authoring, docs, and factory wiring on one
maintainer path.

## First moves

1. Run repo preflight required by `AGENTS.md`:
   - `memory_search`
   - one `aidex` call
   - one `code-index` call
   - `context7` or package metadata when export/codegen tool behavior matters
2. Check `git status --short` before any generated-file work.
3. Inspect existing patterns in:
   - `botocraft/eventbridge/factory.py`
   - one existing wrapper module such as `botocraft/eventbridge/acm.py`
   - one raw package such as `botocraft/eventbridge/raw/acm/`
   - `botocraft/eventbridge/cloudtrail.py` when the event is CloudTrail API-call shaped
4. Read both maintainer runbooks before choosing path:
   - `doc/source/runbook/eventbridge_event_from_schema.rst`
   - `doc/source/runbook/eventbridge_event_from_example.rst`

## Start with dry run

Always begin with schema-library discovery:

```bash
botocraft eventbridge export-service <service> --dry-run
```

If dry run shows the event you need, stay on schema-library path.

If dry run returns nothing useful, or only misses the event you need, switch to
build-from-example path. Do not stop merely because the default registry is
empty.

Default exporter behavior:

- registry search defaults to `aws.events`
- schema prefix defaults to `aws.<service>`
- raw modules land in `botocraft/eventbridge/raw/<service>/`

If `aws.events` misses, say so plainly. Retry with explicit `--registry-name`
values only when user intent or docs suggest alternate registry coverage. If no
registry path yields the event, continue with manual fallback when AWS docs
provide a trustworthy example payload.

## Bulk service authoring (all events for one service)

When the user asks for **all** EventBridge events for a service (or you run
``export-service <service>`` without narrowing to one event):

1. Run ``botocraft eventbridge export-service <service> --dry-run`` and list every
   schema / ``detail-type`` you will support.
2. Implement **each** event with the workflow that fits its shape—do not assume one
   raw pattern fits the whole export.
3. For **every** row whose ``detail-type`` is ``AWS API Call via CloudTrail``,
   stop and apply the CloudTrail section below (flexible raw detail, mixin, tests
   for ``parsed_request``). Other detail-types use the normal schema or
   example-fallback paths.
4. One wrapper module per service (``botocraft/eventbridge/<service>.py``) with a
   single ``EVENT_CLASS_MAP`` covering native events **and** the CloudTrail event.

The user does not need to call out CloudTrail separately. Discovering
``AWS API Call via CloudTrail`` in the dry-run or export output is enough to
trigger the CloudTrail branch for that event.

## Recognize AWS API Call via CloudTrail events

Many services emit the same EventBridge detail type with different envelopes:

| Field | Value for this family |
|-------|------------------------|
| `detail-type` | `AWS API Call via CloudTrail` (same for every service) |
| `source` | `aws.<service>` (for example `aws.acm`, `aws.codepipeline`) |
| `detail.eventSource` | CloudTrail endpoint (for example `acm.amazonaws.com`) |
| `detail.eventName` | API operation (for example `RequestCertificate`) |
| `detail.requestParameters` | **Varies per operation** — do not freeze one shape in raw models |

Factory routing uses **`(source, detail-type)`**, not `detail.eventName`. Each
service still gets its own wrapper class (for example `ACMAWSAPICallViaCloudTrailEvent`).

Registry export may list this event, but exported schemas often overfit one example
operation. For new per-service support, prefer the **flexible CloudTrail detail**
pattern below unless registry output already matches it after inspection.

## Path 1: schema-library workflow

1. Run real export with CLI:

   ```bash
   botocraft eventbridge export-service <service>
   ```

2. Inspect generated raw models in `botocraft/eventbridge/raw/<service>/`.
3. If the event is `AWS API Call via CloudTrail`, read the CloudTrail section in
   the schema runbook and normalize the raw model (see below). Otherwise clean
   up only small readability or import issues after generation.
4. Continue to shared wrapper workflow below.

## Path 2: build from example

Use this fallback when registry discovery cannot supply the event.

1. Find AWS service documentation for EventBridge events.
2. Copy example payload for missing event into local buffer or file.
3. Capture event's human-facing name and `detail-type`.
4. **If `detail-type` is `AWS API Call via CloudTrail`**, skip OpenAPI typing of
   `requestParameters` / `responseElements` from a single example. Use the
   flexible CloudTrail detail template in the example runbook instead.
5. For other events, generate OpenAPI 3.0 schema from example payload, including
   nested fields, reasonable required properties, and concrete types.
6. Save schema locally, for example as `schema.yaml`.
7. Generate raw models with same local toolchain used by exporter (non-CloudTrail
   events only):

   ```bash
   datamodel-codegen \
     --input schema.yaml \
     --input-file-type openapi \
     --output-model-type pydantic_v2.BaseModel \
     --output generated_event.py

   bump-pydantic generated_event.py
   ```

8. Inspect generated file and rename primary event class to Botocraft's
   service-prefixed convention, such as `ECRScanResourceChangeEvent`.
9. Move module into `botocraft/eventbridge/raw/<service>/`.
10. Update re-exports in:
    - `botocraft/eventbridge/raw/<service>/__init__.py`
    - `botocraft/eventbridge/raw/__init__.py`
11. Continue to shared wrapper workflow below.

Stop only when neither registry exports nor a trustworthy documented example
payload can provide raw-model input.

## AWS API Call via CloudTrail — raw model rules

Hand-author or normalize raw modules to match
`botocraft/eventbridge/raw/acm/aws_api_call_via_cloudtrail.py` or
`botocraft/eventbridge/raw/codepipeline/aws_api_call_via_cloudtrail.py`:

- CloudTrail envelope fields (`eventVersion`, `eventTime`, `eventSource`,
  `eventName`, `awsRegion`, …) are typed explicitly.
- `requestParameters` and `responseElements` stay `dict[str, Any] | None`.
- `userIdentity` and nested CloudTrail extras stay flexible (`dict` or optional).
- Docstring states shapes vary by API operation.

Do **not**:

- Generate one rigid Pydantic structure for `requestParameters` from a single
  example (legacy ECR/ECS exports are misleading for other `eventName` values).
- Maintain a hand-written `eventName → RequestModel` registry in raw modules.
- Rely on `aws.cloudtrail` registry exports alone when the delivering source is
  `aws.<service>` — wire the per-service wrapper and `EVENT_CLASS_MAP` entry.

## AWS API Call via CloudTrail — wrapper rules

Wrappers combine:

1. `CloudTrailApiCallMixin` from `botocraft.eventbridge.common` (re-exported from
   `botocraft.eventbridge.cloudtrail`)
2. `EventBridgeEvent`
3. Raw `*AWSAPICallViaCloudTrailEvent` class

Example:

```python
from botocraft.eventbridge.common import CloudTrailApiCallMixin, event_summary
from botocraft.eventbridge.base import EventBridgeEvent
from botocraft.eventbridge.raw.acm import (
    aws_api_call_via_cloudtrail as raw_acm,
)


class ACMAWSAPICallViaCloudTrailEvent(
    CloudTrailApiCallMixin,
    EventBridgeEvent,
    raw_acm.AcmAWSAPICallViaCloudTrailEvent,
):
    ...
```

Register:

```python
("aws.acm", "AWS API Call via CloudTrail"): ACMAWSAPICallViaCloudTrailEvent,
```

### Lazy request typing (`parsed_request`)

Keep `detail.requestParameters` as the raw CloudTrail dict on the event. Optional
botocore-backed parsing lives on the mixin:

- `event.parsed_request()` — `BaseModel` when `eventSource` + `eventName` resolve
  in botocore; otherwise the original dict (or `{}` when absent).
- `event.parsed_request_model(strict=False)` — generated input model type, cached.
- `strict=True` — botocore-required input members become required on the generated
  model (stricter; use only when callers want that tradeoff).

Implementation: `botocraft/eventbridge/cloudtrail.py`. Accepts CloudTrail
camelCase and botocore PascalCase keys (for example `domainName` and `DomainName`).

Document in API RST that `parsed_request()` is best-effort: CloudTrail may omit or
redact fields relative to the live API.

Add service-specific ergonomics on the wrapper only when they do not assume one
`eventName` (for example CodePipeline `pipeline` from resources, not from a single
operation's `requestParameters` shape).

## Shared wrapper workflow

Once raw module exists from either path:

1. Add or update `botocraft/eventbridge/<service>.py` wrapper classes.
2. For `AWS API Call via CloudTrail`, include `CloudTrailApiCallMixin` (see above).
3. Expose one flat `EVENT_CLASS_MAP` constant in wrapper module for factory
   consumption.
4. Update `botocraft/eventbridge/factory.py` only through declarative mapping
   composition, not nested `if` chains.
5. Update docs or runbook references for newly supported event types.
6. Extend targeted tests for factory mapping, wrappers, `parsed_request` when
   CloudTrail-shaped, and authoring helpers.
7. Verify that `EventFactory` now decodes supported event types cleanly.

## Wrapper authoring rules

- Wrapper classes inherit from `EventBridgeEvent` plus raw generated class.
- CloudTrail API-call wrappers also inherit `CloudTrailApiCallMixin`.
- Wrapper behavior stays thin: ergonomic properties, related resource lookups,
  readable `__str__`, and `parsed_request` for operation-aware typing.
- Prefer properties over free functions when behavior belongs to event object.
- Use service-specific class prefixes to avoid cross-service collisions.

## Factory rules

- Each wrapper module exports one flat mapping constant:
  `EVENT_CLASS_MAP[(source, detail-type)] = EventClass`
- `EventFactory` merges those constants.
- Unknown events still fall back to raw dict payloads.

## Tests for CloudTrail API-call events

Minimum coverage when adding or touching this family:

- Factory returns the service wrapper for `("aws.<service>", "AWS API Call via CloudTrail")`.
- `parsed_request()` validates at least one real `eventName` from AWS docs/tests
  (check field access on the returned model).
- `parsed_request()` returns raw dict when `eventName` does not resolve in botocore.

See `tests/eventbridge/test_cloudtrail.py` and service tests such as
`tests/eventbridge/test_acm.py`.

## Caveat

Example-derived OpenAPI schemas are starting points, not full contracts—except for
CloudTrail API-call events, where `requestParameters` must stay flexible in raw
models and operation-specific typing goes through `parsed_request()`.

## Output

End-of-task summary should name:

- whether raw model came from schema-library export, flexible CloudTrail template,
  or example fallback
- raw schemas exported or generated
- whether `CloudTrailApiCallMixin` and `parsed_request` apply
- wrapper modules authored
- factory mappings added
- docs or registration follow-through completed
- tests and repo gates run
