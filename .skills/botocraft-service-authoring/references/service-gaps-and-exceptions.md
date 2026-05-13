# Service Gaps And Exceptions

Repo does not enforce perfect CRUDL symmetry everywhere.

## Models missing normal `get` or `list`

Current exceptions include patterns like:

- list-only readonly resources
- `get`-only style utilities
- resources whose list surface is inherently scoped
- irregular manager methods with capitalized or nonstandard names

Examples worth remembering:

- Bedrock foundation models: `list` only
- STS caller identity: `get` only
- S3 bucket: no normal `get`; many scoped helper methods plus `list`
- Route53 and SQS resources with workflow-specific surfaces
- ElastiCache `Parameter` uses capitalized `List`

## Context-required surfaces

Some resources cannot honestly support global `list` or singular `get` without
inventing semantics AWS does not have.

Examples:

- S3 objects need bucket context
- EventBridge targets need rule context

Model this honestly instead of forcing fake global methods.

## Bespoke pressure

Service is more likely to need bespoke model or manager mixin when:

- identity spans several fields
- AWS surface is split across many calls
- response object is assembled, not returned whole
- normal sync output would otherwise hide important user-facing data

## Authoring stance

- Default to normal Botocraft contract when plausible.
- Accept narrower contract when AWS surface truly requires it.
- Document exception clearly so future service work copies deliberate precedent,
  not accidental inconsistency.
