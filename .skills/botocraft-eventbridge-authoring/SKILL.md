---
name: botocraft-eventbridge-authoring
description: Author Botocraft EventBridge wrappers from AWS schema registry exports, including raw schema export, wrapper module updates, factory registration, and docs follow-through. Use this whenever the user wants to add or expand `botocraft.eventbridge` support for an AWS service, export EventBridge schemas, generate raw event models, wire new wrapper classes, or extend EventFactory mappings.
---

# Botocraft EventBridge Authoring

Use this skill when task is specifically about Botocraft EventBridge support.
Keep raw schema export, wrapper authoring, docs, and factory wiring on one path.

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

## Shared implementation path

Use shared exporter path first:

```bash
botocraft eventbridge export-service <service>
```

Default behavior:

- registry search defaults to `aws.events`
- schema prefix defaults to `aws.<service>`
- raw modules land in `botocraft/eventbridge/raw/<service>/`

If the queried AWS Schema Registry returns no schemas for the requested service,
stop and tell the user there are no schemas in the registry. Do not continue to
manual schema authoring or wrapper work inside this skill.

## Workflow

1. Export raw schemas with CLI.
2. If no schemas are returned, stop and report that the AWS Schema Registry has
   no schemas for the requested service.
3. Inspect generated raw models in `botocraft/eventbridge/raw/<service>/`.
4. Author or update `botocraft/eventbridge/<service>.py` wrapper classes.
5. Expose one mapping constant in wrapper module for factory consumption.
6. Update `botocraft/eventbridge/factory.py` only through declarative mapping
   composition, not nested `if` chains.
7. Update docs or runbook references for newly supported event types.
8. Extend event registration or caller paths that consume new wrapper types.

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

## Output

End-of-task summary should name:

- raw schemas exported
- wrapper modules authored
- factory mappings added
- docs or registration follow-through completed
- tests and repo gates run
