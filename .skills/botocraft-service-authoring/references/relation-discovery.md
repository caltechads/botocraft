# Relation Discovery Workflow

Use this reference when Botocraft service authoring needs help finding likely
`relations:` between primary models.

## Two-stage rule

Never collapse discovery and implementation into one step unless the user
explicitly asks to skip review.

Stage 1:

- discover likely relations
- present them for keep/drop review
- call out confidence, evidence, and blockers

Stage 2:

- implement only approved relations
- leave uncertain cases unimplemented
- explain why any likely-looking field stayed raw

## Stage 1 heuristics

Start from each primary model.
Inspect its direct fields, then recurse through nested structures and list
members looking for likely foreign identifiers.

High-signal suffixes:

- `id`
- `ids`
- `arn`
- `arns`
- `name`
- `names`

Case-insensitive matching is fine.

Exclude self-identity fields first:

- the model `primary_key`
- the model `arn_key`
- the model `name_key`
- obvious aliases or renames of those same identity fields

When a likely identifier field is found:

1. strip the suffix
2. normalize the stem
3. look for a matching botocore model name
4. map that to the Botocraft public primary model name

When mapping names, remember that Botocraft can expose a public model name via
`alternate_name` that differs from the underlying botocore shape name.

Only suggest a `relation` when the target is a primary model.
If the likely target is only a secondary model, mention it as supporting
evidence but do not suggest a relation yet.

## Many-vs-one hints

Suggest `many: true` when one or more are true:

- the source field is a list shape
- the field name uses a plural suffix such as `Ids`, `Arns`, or `Names`
- existing repo patterns point to list-style lookup

Otherwise prefer singular relation candidates first.

## AWS-doc-assisted fuzzy pass

After suffix-based discovery, do a second fuzzy pass for relationships that are
real but not obvious from field endings alone.

Prefer `aws-knowledge-mcp-server` when available.
If it is unavailable and the user declines installation, continue with official
AWS docs on the web.

Good fuzzy cases:

- composite identifiers such as Application Auto Scaling `ResourceId`
- ARN fragments that require regex extraction
- nested service references such as ECS load balancer target groups
- fields whose docs clearly describe another AWS resource without ending in
  `name`, `arn`, or `id`

Do not let fuzzy discovery silently become implementation.
Keep it in the review list until the user approves it.

## Candidate review output

Present relation candidates as a compact review list or table with:

- source primary model
- field path
- proposed relation name
- target primary model
- proposed transformer shape
- whether it looks singular or `many`
- confidence: high, medium, or low
- evidence
- blocker, if any

## Confidence rubric

High:

- direct suffix hit
- target maps cleanly to a primary model
- expected manager lookup path looks stable

Medium:

- suffix hit but relation naming or lookup path is a little ambiguous
- target exists but mapping or plurality needs judgment

Low:

- fuzzy docs-only hint
- composite parsing or regex extraction still speculative
- target or lookup path remains unclear

## Implementation guardrails

After review, implement only approved relations.

Prefer:

- mapping transformer first
- regex transformer only when extraction is structured and stable
- property instead of relation when the result is only a derived local value
- model mixin or manager mixin when relation would otherwise require contorted
  YAML or several calls
