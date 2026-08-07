# Add AWS Managed Grafana Support

## Goal

Add Botocraft support for AWS Managed Grafana (`grafana`) workspaces, service
accounts, service account tokens, and common workspace administration
operations. Token automation must follow
`docs/adr/0001-delete-previous-amg-service-account-token-during-rotation.md`.

## Scope

- Add source-of-truth service config under `botocraft/data/grafana/`.
- Add handwritten manager helpers under `botocraft/mixins/grafana.py` only when
  YAML generation cannot express the workflow cleanly.
- Regenerate `botocraft/services/grafana.py` and generated service docs with
  full `botocraft sync`.
- Add focused tests for token rotation and shape parsing.

## Public Model

- `ManagedGrafanaWorkspace`
  - Backed by botocore `WorkspaceDescription`.
  - Primary key: `id`.
  - Name key: `name`.
  - Expose tag data as `Tags`, normalized from AWS `tags`.
- `ManagedGrafanaServiceAccount`
  - Backed by `ServiceAccountSummary`.
  - Primary key: `id`.
  - Name key: `name`.
  - Operations are workspace-scoped.
- `ManagedGrafanaServiceAccountToken`
  - Backed by `ServiceAccountTokenSummary`.
  - Primary key: `id`.
  - Name key: `name`.
  - Operations are workspace-and-service-account scoped.
- `ManagedGrafanaServiceAccountTokenWithKey`
  - Backed by `ServiceAccountTokenSummaryWithKey`.
  - Supporting return model, not the listable primary token resource.
  - Returned by create and rotate paths because the token key is visible only at
    creation time.

Do not add a public model or manager workflow for legacy workspace API keys.

## Manager Surface

### Workspace Manager

- `create` -> `create_workspace`, returning `ManagedGrafanaWorkspace`.
- `get` -> `describe_workspace`, returning `ManagedGrafanaWorkspace`.
- `list` -> manager mixin that calls `list_workspaces`, then hydrates each
  summary with `describe_workspace` so callers receive full
  `ManagedGrafanaWorkspace` models.
- `update` -> `update_workspace`, returning `ManagedGrafanaWorkspace`.
- `delete` -> `delete_workspace`, returning `ManagedGrafanaWorkspace`.
- `describe_authentication` -> `describe_workspace_authentication`.
- `update_authentication` -> `update_workspace_authentication`.
- `describe_configuration` -> `describe_workspace_configuration`.
- `update_configuration` -> `update_workspace_configuration`.
- `associate_license` -> `associate_license`.
- `disassociate_license` -> `disassociate_license`.
- `list_permissions` -> `list_permissions`.
- `update_permissions` -> `update_permissions`.
- `list_versions` -> `list_versions`.

### Service Account Manager

- `create` -> `create_workspace_service_account`.
- `list` -> `list_workspace_service_accounts`.
- `delete` -> `delete_workspace_service_account`.
- Do not add `get` or `update`; AWS Managed Grafana does not expose those
  service account operations.

### Service Account Token Manager

- `create` -> `create_workspace_service_account_token`, returning
  `ManagedGrafanaServiceAccountTokenWithKey`.
- `list` -> `list_workspace_service_account_tokens`.
- `delete` -> `delete_workspace_service_account_token`.
- `rotate` -> handwritten manager mixin:
  - call `create_workspace_service_account_token`;
  - call `delete_workspace_service_account_token` with the previous token id;
  - return `ManagedGrafanaServiceAccountTokenWithKey`;
  - if delete fails, let the AWS exception raise and do not return the new key.
- Do not add `update`; token update means rotation in this domain.

## Implementation Steps

1. Inspect current botocore `grafana` operation input/output shapes for every
   manager method above.
2. Author `botocraft/data/grafana/models.yml` with the smallest explicit
   primary and secondary shape overrides needed to generate imports cleanly.
3. Author `botocraft/data/grafana/managers.yml` for direct operations that map
   cleanly to one AWS call.
4. Add `botocraft/mixins/grafana.py` for token rotation and any context-scoped
   list/get behavior that generation cannot express safely.
5. Run full `botocraft sync`.
6. Inspect generated `botocraft/services/grafana.py` for:
   - wrong `response_attr`;
   - `None(**_response)` or empty-output construction bugs;
   - stale `tags` instead of `Tags`;
   - bad forward refs or collisions;
   - accidental workspace API key public helpers.
7. Add focused tests for:
   - token rotation call order and delete-after-create behavior;
   - delete failure raising without returning the token;
   - service model imports and representative payload validation;
   - absence of workspace API key helpers.
8. Run required gates:
   - `.venv/bin/ruff check` on touched Python files;
   - `.venv/bin/mypy` on touched Python files or package path needed by mypy;
   - `make napoleon-gate`;
   - focused pytest for new tests.

## Security Checks

- Token key appears only on `ManagedGrafanaServiceAccountTokenWithKey`, not on
  list-returned token summaries.
- Rotation deletes the exact previous token id passed by the caller.
- No automatic fallback to legacy workspace API keys.
- No logging, repr customization, or docs examples should print real token
  values.

## Open Risks

- Workspace create/update input names (`workspaceName`, `workspaceDescription`,
  etc.) do not match response model field names (`name`, `description`, etc.);
  generation may need explicit field overrides or a manager mixin.
- Workspace list returns `WorkspaceSummary`, not `WorkspaceDescription`; list
  must hydrate via `describe_workspace` to preserve the public workspace model.
- Service account and token managers are context-scoped; generated zero-context
  `list()` may be impossible, so handwritten mixins may be required.
