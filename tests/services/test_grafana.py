import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# NOTE: ``botocraft.services.grafana`` must be imported before
# ``botocraft.mixins.grafana`` -- importing the mixins module first (before
# ``botocraft.services`` has finished initializing) triggers a circular
# import through ``botocraft.mixins.common``. ruff's import sorter would
# otherwise reorder these two imports alphabetically and reintroduce the
# circular import, so isort is disabled for this block.
# ruff: isort: off
import botocraft.services.grafana as grafana_service
from botocraft.services.grafana import (
    ManagedGrafanaServiceAccount,
    ManagedGrafanaServiceAccountManager,
    ManagedGrafanaServiceAccountToken,
    ManagedGrafanaServiceAccountTokenManager,
    ManagedGrafanaServiceAccountTokenWithKey,
    ManagedGrafanaWorkspace,
    ManagedGrafanaWorkspaceManager,
)

import botocraft.mixins.grafana as grafana_mixins
# ruff: isort: on


def _token_create_response(
    *,
    token_id: str,
    name: str,
    key: str,
    service_account_id: str,
    workspace_id: str,
) -> dict[str, object]:
    """Shape a representative ``CreateWorkspaceServiceAccountTokenResponse``."""
    return {
        "serviceAccountToken": {
            "id": token_id,
            "name": name,
            "key": key,
        },
        "serviceAccountId": service_account_id,
        "workspaceId": workspace_id,
    }


class TestGrafanaShadowedFieldAliases:
    """
    ``ManagedGrafanaWorkspace``, ``ManagedGrafanaServiceAccount``, and
    ``ManagedGrafanaServiceAccountToken`` all wrap botocore shapes whose wire
    field is literally ``name``.  Botocraft renames the Python attribute
    (``workspaceName``/``serviceAccountName``/``tokenName``) with
    ``alias="name"`` so it doesn't collide with the inherited
    :py:attr:`~botocraft.services.abstract.PrimaryBoto3Model.name` property.
    This mirrors ``TestBedrockShadowedFieldAliases`` in ``test_bedrock.py``.
    """

    def test_primary_model_name_property_uses_renamed_field(self) -> None:
        workspace = ManagedGrafanaWorkspace.model_construct(
            id="g-1234abcd",
            workspaceName="Test Workspace",
            session=None,
        )
        service_account = ManagedGrafanaServiceAccount.model_construct(
            id="sa-1",
            serviceAccountName="Test Service Account",
            session=None,
        )
        token = ManagedGrafanaServiceAccountToken.model_construct(
            id="token-1",
            tokenName="Test Token",
            session=None,
        )

        assert workspace.name == "Test Workspace"
        assert workspace.model_dump(by_alias=True)["name"] == "Test Workspace"
        assert service_account.name == "Test Service Account"
        assert (
            service_account.model_dump(by_alias=True)["name"]
            == "Test Service Account"
        )
        assert token.name == "Test Token"
        assert token.model_dump(by_alias=True)["name"] == "Test Token"

    def test_service_imports_do_not_emit_shadow_warnings(self) -> None:
        result = subprocess.run(
            [sys.executable, "-Wdefault", "-c", "from botocraft.services import *"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert "shadows an attribute" not in result.stderr


class TestManagedGrafanaServiceAccountTokenManagerRotate:
    """Tests for the handwritten ``rotate()`` on the token manager mixin."""

    @patch("boto3.client")
    def test_rotate_creates_before_deleting_and_returns_new_key(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        call_order: list[str] = []

        def _create(**_kwargs: object) -> dict[str, object]:
            call_order.append("create")
            return _token_create_response(
                token_id="new-token",  # noqa: S106
                name="rotated",
                key="new-key-value",
                service_account_id="sa-1",
                workspace_id="ws-1",
            )

        def _delete(**_kwargs: object) -> dict[str, object]:
            call_order.append("delete")
            return {}

        mock_client.create_workspace_service_account_token.side_effect = _create
        mock_client.delete_workspace_service_account_token.side_effect = _delete
        mock_boto3_client.return_value = mock_client

        manager = ManagedGrafanaServiceAccountTokenManager()
        result = manager.rotate(
            name="rotated",
            secondsToLive=3600,
            serviceAccountId="sa-1",
            workspaceId="ws-1",
            previous_token_id="old-token",  # noqa: S106
        )

        # create must happen strictly before delete.
        assert call_order == ["create", "delete"]

        # the exact previous token id must be passed through to delete.
        delete_kwargs = (
            mock_client.delete_workspace_service_account_token.call_args.kwargs
        )
        assert delete_kwargs["tokenId"] == "old-token"
        assert delete_kwargs["serviceAccountId"] == "sa-1"
        assert delete_kwargs["workspaceId"] == "ws-1"

        # the caller gets back the new token's key.
        assert isinstance(result, ManagedGrafanaServiceAccountTokenWithKey)
        assert result.key == "new-key-value"
        assert result.id == "new-token"

    @patch("boto3.client")
    def test_rotate_propagates_delete_failure_and_does_not_return(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_workspace_service_account_token.return_value = (
            _token_create_response(
                token_id="new-token",  # noqa: S106
                name="rotated",
                key="new-key-value",
                service_account_id="sa-1",
                workspace_id="ws-1",
            )
        )
        mock_client.delete_workspace_service_account_token.side_effect = ClientError(
            {"Error": {"Code": "InternalServerException", "Message": "boom"}},
            "DeleteWorkspaceServiceAccountToken",
        )
        mock_boto3_client.return_value = mock_client

        manager = ManagedGrafanaServiceAccountTokenManager()

        result = None
        with pytest.raises(ClientError):
            result = manager.rotate(
                name="rotated",
                secondsToLive=3600,
                serviceAccountId="sa-1",
                workspaceId="ws-1",
                previous_token_id="old-token",  # noqa: S106
            )

        # the exception must propagate unchanged, and the caller must never
        # receive the new token/key when delete fails.
        assert result is None
        mock_client.create_workspace_service_account_token.assert_called_once()
        mock_client.delete_workspace_service_account_token.assert_called_once()


class TestModelPayloadParsing:
    """Models import cleanly and validate representative botocore payloads."""

    def test_workspace_model_parses_representative_payload(self) -> None:
        workspace = ManagedGrafanaWorkspace(
            id="g-1234abcd",
            name="demo",
            status="ACTIVE",
            created="2024-01-01T00:00:00+00:00",
            modified="2024-01-02T00:00:00+00:00",
            endpoint="https://g-1234abcd.grafana-workspace.us-west-2.amazonaws.com",
            grafanaVersion="10.4",
            dataSources=["CLOUDWATCH"],
            authentication={"providers": ["AWS_SSO"]},
            tags={"Environment": "test"},
        )

        assert workspace.id == "g-1234abcd"
        assert workspace.Tags == {"Environment": "test"}
        assert workspace.authentication.providers == ["AWS_SSO"]

    def test_service_account_model_parses_representative_payload(self) -> None:
        # CreateWorkspaceServiceAccountResponse is flat (id/name/grafanaRole/
        # workspaceId) and has no isDisabled -- this payload instead mirrors
        # ServiceAccountSummary, the shape used everywhere else (list/get).
        service_account = ManagedGrafanaServiceAccount(
            id="sa-1",
            name="automation",
            isDisabled="false",
            grafanaRole="ADMIN",
            workspaceId="ws-1",
        )

        assert service_account.workspaceId == "ws-1"
        assert service_account.isDisabled == "false"

    def test_service_account_token_model_parses_representative_payload(self) -> None:
        # ServiceAccountTokenSummary has no ``key`` field.
        token = ManagedGrafanaServiceAccountToken(
            id="token-1",
            name="ci-token",
            createdAt="2024-01-01T00:00:00+00:00",
            expiresAt="2024-02-01T00:00:00+00:00",
            serviceAccountId="sa-1",
            workspaceId="ws-1",
        )

        assert token.serviceAccountId == "sa-1"
        assert token.workspaceId == "ws-1"
        assert not hasattr(token, "key")

    def test_service_account_token_with_key_model_parses_representative_payload(
        self,
    ) -> None:
        token = ManagedGrafanaServiceAccountTokenWithKey(
            id="token-1",
            name="ci-token",
            key="secret-key-value",
            serviceAccountId="sa-1",
            workspaceId="ws-1",
        )

        assert token.key == "secret-key-value"


class TestNoLegacyWorkspaceApiKeySupport:
    """AWS's legacy workspace API key operations must not be modeled anywhere."""

    def test_no_workspace_api_key_symbols_in_service_module(self) -> None:
        names = dir(grafana_service)

        assert not any("WorkspaceApiKey" in name for name in names)
        assert not any("workspace_api_key" in name.lower() for name in names)

    def test_no_workspace_api_key_symbols_in_mixin_module(self) -> None:
        names = dir(grafana_mixins)

        assert not any("WorkspaceApiKey" in name for name in names)
        assert not any("workspace_api_key" in name.lower() for name in names)

    def test_no_workspace_api_key_manager_methods(self) -> None:
        managers = [
            grafana_service.ManagedGrafanaWorkspaceManager,
            grafana_service.ManagedGrafanaServiceAccountManager,
            grafana_service.ManagedGrafanaServiceAccountTokenManager,
        ]
        for manager_cls in managers:
            for attr_name in dir(manager_cls):
                assert "workspace_api_key" not in attr_name.lower()
                assert "WorkspaceApiKey" not in attr_name


class TestSecurityKeyFieldPlacement:
    """The plaintext token ``key`` may only live on the *WithKey model."""

    def test_key_not_on_summary_token_model(self) -> None:
        assert "key" not in ManagedGrafanaServiceAccountToken.model_fields

    def test_key_present_only_on_with_key_model(self) -> None:
        assert "key" in ManagedGrafanaServiceAccountTokenWithKey.model_fields

    def test_key_field_excluded_from_default_repr(self) -> None:
        # The plaintext key must never be leaked by print()/repr() of a
        # ManagedGrafanaServiceAccountTokenWithKey instance.
        token = ManagedGrafanaServiceAccountTokenWithKey(
            id="token-1",
            name="ci-token",
            key="super-secret-value",
            serviceAccountId="sa-1",
            workspaceId="ws-1",
        )

        assert "super-secret-value" not in repr(token)
        assert ManagedGrafanaServiceAccountTokenWithKey.model_fields["key"].repr is False


class TestManagedGrafanaWorkspaceManagerList:
    """Tests for the handwritten ``list()`` on the workspace manager mixin."""

    @patch("boto3.client")
    def test_list_paginates_and_hydrates_full_workspaces(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()

        # ListWorkspaces only returns the lean WorkspaceSummary shape.
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"workspaces": [{"id": "g-1"}, {"id": "g-2"}]},
        ]
        mock_client.get_paginator.return_value = mock_paginator

        def _describe_workspace(*, workspaceId: str) -> dict[str, object]:  # noqa: N803
            return {
                "workspace": {
                    "id": workspaceId,
                    "name": f"name-{workspaceId}",
                    "status": "ACTIVE",
                    "created": "2024-01-01T00:00:00+00:00",
                    "modified": "2024-01-02T00:00:00+00:00",
                    "endpoint": f"https://{workspaceId}.grafana-workspace.example.com",
                    "grafanaVersion": "10.4",
                    "dataSources": ["CLOUDWATCH"],
                    "authentication": {"providers": ["AWS_SSO"]},
                }
            }

        mock_client.describe_workspace.side_effect = _describe_workspace
        mock_boto3_client.return_value = mock_client

        manager = ManagedGrafanaWorkspaceManager()
        results = list(manager.list())

        mock_client.get_paginator.assert_called_once_with("list_workspaces")
        assert mock_client.describe_workspace.call_count == 2
        assert [w.id for w in results] == ["g-1", "g-2"]
        # We got back full ManagedGrafanaWorkspace objects, not the leaner
        # WorkspaceSummary shape -- e.g. ``status`` only exists on the full
        # shape.
        for workspace in results:
            assert isinstance(workspace, ManagedGrafanaWorkspace)
            assert workspace.status == "ACTIVE"
            assert workspace.name == f"name-{workspace.id}"


class TestServiceAccountTokenListContextReattachment:
    """Tests for ``service_account_tokens_add_context``."""

    @patch("boto3.client")
    def test_list_reattaches_workspace_and_service_account_ids_positionally(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "serviceAccountTokens": [
                    {
                        "id": "token-1",
                        "name": "ci-token-1",
                        "createdAt": "2024-01-01T00:00:00+00:00",
                        "expiresAt": "2024-02-01T00:00:00+00:00",
                    },
                    {
                        "id": "token-2",
                        "name": "ci-token-2",
                        "createdAt": "2024-01-01T00:00:00+00:00",
                        "expiresAt": "2024-02-01T00:00:00+00:00",
                    },
                ],
                # These reflect the response envelope, not any values the
                # caller passed -- they exist to prove the decorator uses
                # the *positional call arguments*, not this envelope data,
                # to populate scope.
                "serviceAccountId": "sa-envelope-should-be-ignored",
                "workspaceId": "ws-envelope-should-be-ignored",
            },
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = ManagedGrafanaServiceAccountTokenManager()
        # ``list()``'s positional signature is
        # ``list(self, serviceAccountId, workspaceId)`` -- the
        # ``service_account_tokens_add_context`` decorator relies on that
        # exact positional order (serviceAccountId at position 0,
        # workspaceId at position 1) to reattach scope, so this test calls
        # it positionally, not via keywords, to pin that contract.
        results = list(manager.list("sa-1", "ws-1"))

        assert len(results) == 2
        for token, expected_name in zip(results, ("ci-token-1", "ci-token-2"), strict=True):
            assert isinstance(token, ManagedGrafanaServiceAccountToken)
            assert token.serviceAccountId == "sa-1"
            assert token.workspaceId == "ws-1"
            # ServiceAccountTokenSummary never carries the plaintext key.
            assert not hasattr(token, "key")
            # Regression: the ``model_dump()``/reconstruct round-trip in
            # ``service_account_tokens_add_context`` must not silently drop
            # ``name`` (aliased to the ``tokenName`` Python attribute).
            assert token.name == expected_name
            assert token.tokenName == expected_name


class TestServiceAccountListContextReattachment:
    """Tests for ``service_accounts_add_workspace_context``."""

    @patch("boto3.client")
    def test_list_reattaches_workspace_id_and_preserves_name(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "serviceAccounts": [
                    {
                        "id": "sa-1",
                        "name": "ci-service-account-1",
                        "grafanaRole": "ADMIN",
                        "isDisabled": "false",
                    },
                    {
                        "id": "sa-2",
                        "name": "ci-service-account-2",
                        "grafanaRole": "EDITOR",
                        "isDisabled": "false",
                    },
                ],
                # This reflects the response envelope, not the value the
                # caller passed -- it exists to prove the decorator uses the
                # caller-supplied ``workspaceId``, not this envelope value.
                "workspaceId": "ws-envelope-should-be-ignored",
            },
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_boto3_client.return_value = mock_client

        manager = ManagedGrafanaServiceAccountManager()
        results = list(manager.list("ws-1"))

        assert len(results) == 2
        for service_account, expected_name in zip(
            results, ("ci-service-account-1", "ci-service-account-2"), strict=True
        ):
            assert isinstance(service_account, ManagedGrafanaServiceAccount)
            assert service_account.workspaceId == "ws-1"
            # Regression: the ``model_dump()``/reconstruct round-trip in
            # ``service_accounts_add_workspace_context`` must not silently
            # drop ``name`` (aliased to the ``serviceAccountName`` Python
            # attribute).
            assert service_account.name == expected_name
            assert service_account.serviceAccountName == expected_name


class TestServiceAccountCreateIsDisabledDefault:
    """
    Tests for the ``isDisabled`` default set by
    ``service_account_create_to_service_account``.
    """

    @patch("boto3.client")
    def test_create_defaults_isdisabled_to_string_false(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_workspace_service_account.return_value = {
            "id": "sa-1",
            "name": "automation",
            "grafanaRole": "ADMIN",
            "workspaceId": "ws-1",
        }
        mock_boto3_client.return_value = mock_client

        manager = ManagedGrafanaServiceAccountManager()
        model = ManagedGrafanaServiceAccount(
            id="",
            name="automation",
            isDisabled="false",
            grafanaRole="ADMIN",
            workspaceId="ws-1",
        )
        result = manager.create(model)

        assert isinstance(result, ManagedGrafanaServiceAccount)
        # isDisabled is a botocore String shape (not a bool), so the
        # correct default is the *string* "false", not the Python bool-ish
        # "False".
        assert result.isDisabled == "false"
        assert result.isDisabled != "False"


class TestCompositePkAndDelete:
    """
    Tests for the composite ``pk`` on the context-scoped grafana models.

    Neither ``ManagedGrafanaServiceAccount`` nor
    ``ManagedGrafanaServiceAccountToken`` can be deleted with a bare ``id``
    -- AWS Managed Grafana's delete operations for both are scoped to their
    parent workspace (and, for tokens, also to the parent service account).
    ``PrimaryBoto3Model.delete()`` calls ``self.objects.delete(**self.pk)``
    when ``pk`` is an ``OrderedDict``, so ``pk`` must map to the exact
    keyword arguments the generated ``delete()`` manager methods expect.
    """

    def test_service_account_pk_matches_delete_signature(self) -> None:
        service_account = ManagedGrafanaServiceAccount(
            id="sa-1",
            name="automation",
            isDisabled="false",
            grafanaRole="ADMIN",
            workspaceId="ws-1",
        )

        assert dict(service_account.pk) == {
            "serviceAccountId": "sa-1",
            "workspaceId": "ws-1",
        }

    @patch("boto3.client")
    def test_service_account_delete_calls_through_with_scoping_kwargs(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.delete_workspace_service_account.return_value = {}
        mock_boto3_client.return_value = mock_client

        service_account = ManagedGrafanaServiceAccount(
            id="sa-1",
            name="automation",
            isDisabled="false",
            grafanaRole="ADMIN",
            workspaceId="ws-1",
        )
        service_account.delete()

        mock_client.delete_workspace_service_account.assert_called_once_with(
            serviceAccountId="sa-1", workspaceId="ws-1"
        )

    def test_service_account_token_pk_matches_delete_signature(self) -> None:
        token = ManagedGrafanaServiceAccountToken(
            id="token-1",
            name="ci-token",
            createdAt="2024-01-01T00:00:00+00:00",
            expiresAt="2024-02-01T00:00:00+00:00",
            serviceAccountId="sa-1",
            workspaceId="ws-1",
        )

        assert dict(token.pk) == {
            "tokenId": "token-1",
            "serviceAccountId": "sa-1",
            "workspaceId": "ws-1",
        }

    @patch("boto3.client")
    def test_service_account_token_delete_calls_through_with_scoping_kwargs(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.delete_workspace_service_account_token.return_value = {}
        mock_boto3_client.return_value = mock_client

        token = ManagedGrafanaServiceAccountToken(
            id="token-1",
            name="ci-token",
            createdAt="2024-01-01T00:00:00+00:00",
            expiresAt="2024-02-01T00:00:00+00:00",
            serviceAccountId="sa-1",
            workspaceId="ws-1",
        )
        token.delete()

        mock_client.delete_workspace_service_account_token.assert_called_once_with(
            tokenId="token-1", serviceAccountId="sa-1", workspaceId="ws-1"
        )
