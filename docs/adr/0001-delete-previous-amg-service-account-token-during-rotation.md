# Delete Previous AMG Service Account Token During Rotation

Botocraft will support AWS Managed Grafana automation with service account
tokens, not legacy workspace API keys. A rotation call creates a replacement
service account token, then always deletes the previous token id supplied by the
caller.

This intentionally treats the DevOps caller as the owner of sequencing around
secret storage and Terraform handoff. If deletion fails after token creation,
Botocraft lets the AWS error raise and does not try to return the newly-created
token key through a partial-success path.

## Considered Options

- Keep both old and new tokens active so callers can store the new key before
  deleting the old one.
- Delete the old token only when callers pass an explicit delete flag.
- Always delete the previous token id as part of rotation.

We chose automatic deletion because this workflow is for automation that already
controls the secret-store write and Terraform usage, and because expired or
unused service account tokens still count toward AWS Managed Grafana token
quotas until deleted.

## Consequences

- Callers must pass the exact previous token id they want revoked.
- Callers must be prepared for deletion failure to surface as an exception after
  token creation.
- Botocraft should expose create, list, delete, and rotate token operations, but
  not an update-token operation because AWS Managed Grafana does not provide one.
- Botocraft should not build support for legacy workspace API keys for this
  workflow.
