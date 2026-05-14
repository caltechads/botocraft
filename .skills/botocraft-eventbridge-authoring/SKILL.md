---
name: botocraft-eventbridge-authoring
description: Author Botocraft EventBridge support for AWS services, whether schemas come from AWS Schema Registry or must be built from AWS documentation examples. Use this whenever the user wants to add or expand `botocraft.eventbridge` support, export EventBridge schemas, diagnose missing schema-library coverage, generate raw event models from example payloads, wire wrapper classes, extend EventFactory mappings, or finish docs and test follow-through for new event types.
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
   - one existing wrapper module such as `botocraft/eventbridge/ecs.py`
   - one raw package such as `botocraft/eventbridge/raw/ecs/`
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

## Path 1: schema-library workflow

1. Run real export with CLI:

   ```bash
   botocraft eventbridge export-service <service>
   ```

2. Inspect generated raw models in `botocraft/eventbridge/raw/<service>/`.
3. Clean up only small readability or import issues after generation.
4. Continue to shared wrapper workflow below.

## Path 2: build from example

Use this fallback when registry discovery cannot supply the event.

1. Find AWS service documentation for EventBridge events.
2. Copy example payload for missing event into local buffer or file.
3. Capture event's human-facing name and `detail-type`.
4. Generate OpenAPI 3.0 schema from example payload, including nested fields,
   reasonable required properties, and concrete types.
5. Save schema locally, for example as `schema.yaml`.
6. Generate raw models with same local toolchain used by exporter:

   ```bash
   datamodel-codegen \
     --input schema.yaml \
     --input-file-type openapi \
     --output-model-type pydantic_v2.BaseModel \
     --output generated_event.py

   bump-pydantic generated_event.py
   ```

7. Inspect generated file and rename primary event class to Botocraft's
   service-prefixed convention, such as `ECRScanResourceChangeEvent`.
8. Move module into `botocraft/eventbridge/raw/<service>/`.
9. Update re-exports in:
   - `botocraft/eventbridge/raw/<service>/__init__.py`
   - `botocraft/eventbridge/raw/__init__.py`
10. Continue to shared wrapper workflow below.

Stop only when neither registry exports nor a trustworthy documented example
payload can provide raw-model input.

## Shared wrapper workflow

Once raw module exists from either path:

1. Add or update `botocraft/eventbridge/<service>.py` wrapper classes.
2. Expose one flat `EVENT_CLASS_MAP` constant in wrapper module for factory
   consumption.
3. Update `botocraft/eventbridge/factory.py` only through declarative mapping
   composition, not nested `if` chains.
4. Update docs or runbook references for newly supported event types.
5. Extend targeted tests for factory mapping, wrappers, and authoring helpers.
6. Verify that `EventFactory` now decodes supported event types cleanly.

## Wrapper authoring rules

- Wrapper classes inherit from `EventBridgeEvent` plus raw generated class.
- Wrapper behavior stays thin: ergonomic properties, related resource lookups,
  and readable `__str__`.
- Prefer properties over free functions when behavior belongs to event object.
- Use service-specific class prefixes to avoid cross-service collisions.

## Factory rules

- Each wrapper module exports one flat mapping constant:
  `EVENT_CLASS_MAP[(source, detail-type)] = EventClass`
- `EventFactory` merges those constants.
- Unknown events still fall back to raw dict payloads.

## Caveat

Example-derived OpenAPI schemas are starting points, not full contracts.
Optional fields may look required, some real-world fields may be missing, and
nested shapes may need cleanup after real traffic appears.

## Output

End-of-task summary should name:

- whether raw model came from schema-library export or example fallback
- raw schemas exported or generated
- wrapper modules authored
- factory mappings added
- docs or registration follow-through completed
- tests and repo gates run
