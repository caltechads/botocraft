# Monolith Snapshot

Before this split, `botocraft-service-authoring` was one large `SKILL.md`
covering:

- repo preflight
- dirty-tree safeguards
- core rules
- live AWS vs local botocore drift
- YAML type-override gotchas
- verification workflow
- generated-service quality-gate interpretation
- detailed workflow for discovery, models, managers, mixins, and summary
- Bedrock enum-drift worked example

Use git history or prior workspace snapshot if you need exact old-body text for
an eval baseline. This file exists so eval design and future maintainers know
the split intentionally replaced one monolith with routed leaf skills plus
references.
