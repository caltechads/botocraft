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
    ManagedGrafanaServiceAccountToken,
    ManagedGrafanaServiceAccountTokenManager,
    ManagedGrafanaServiceAccountTokenWithKey,
    ManagedGrafanaWorkspace,
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
