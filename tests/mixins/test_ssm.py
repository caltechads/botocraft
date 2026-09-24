"""Tests for the SSM Parameter tag-hydration/tag-write decorators."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ssm import Parameter, ParameterManager


def _parameter_payload() -> dict:
    return {
        "Name": "/grafana/hub/provisioning-token",
        "Type": "SecureString",
        "Value": "shh",
        "Version": 3,
    }


class TestParameterTags:
    @patch("boto3.client")
    def test_get_hydrates_tags(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.get_parameters.return_value = {
            "Parameters": [_parameter_payload()]
        }
        mock_client.list_tags_for_resource.return_value = {
            "TagList": [{"Key": "GrafanaTokenId", "Value": "tok-123"}]
        }
        mock_boto3_client.return_value = mock_client

        manager = ParameterManager()
        result = manager.get("/grafana/hub/provisioning-token")

        assert result is not None
        assert result.Tags is not None
        assert result.tags["GrafanaTokenId"] == "tok-123"
        mock_client.list_tags_for_resource.assert_called_once_with(
            ResourceType="Parameter",
            ResourceId="/grafana/hub/provisioning-token",
        )

    @patch("boto3.client")
    def test_get_returns_none_without_calling_list_tags(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_parameters.return_value = {"Parameters": []}
        mock_boto3_client.return_value = mock_client

        manager = ParameterManager()
        result = manager.get("/does/not/exist")

        assert result is None
        mock_client.list_tags_for_resource.assert_not_called()

    @patch("boto3.client")
    def test_update_writes_tags_via_add_tags_to_resource(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.put_parameter.return_value = {"Version": 4}
        mock_boto3_client.return_value = mock_client

        manager = ParameterManager()
        model = Parameter(
            Name="/grafana/hub/provisioning-token",
            Value="new-value",
            Type="SecureString",
            Tags=[{"Key": "GrafanaTokenId", "Value": "tok-456"}],
        )
        manager.update(model, Overwrite=True)

        _, put_kwargs = mock_client.put_parameter.call_args
        assert "Tags" not in put_kwargs
        mock_client.add_tags_to_resource.assert_called_once_with(
            ResourceType="Parameter",
            ResourceId="/grafana/hub/provisioning-token",
            Tags=[{"Key": "GrafanaTokenId", "Value": "tok-456"}],
        )

    @patch("boto3.client")
    def test_create_forwards_tags_via_model_field(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.put_parameter.return_value = {"Version": 1}
        mock_boto3_client.return_value = mock_client

        manager = ParameterManager()
        model = Parameter(
            Name="/grafana/hub/provisioning-token",
            Value="initial-value",
            Type="SecureString",
            Tags=[{"Key": "Foo", "Value": "Bar"}],
        )
        manager.create(model)

        _, put_kwargs = mock_client.put_parameter.call_args
        assert put_kwargs["Tags"] == [{"Key": "Foo", "Value": "Bar"}]

    @patch("boto3.client")
    def test_update_skips_add_tags_when_none_present(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.put_parameter.return_value = {"Version": 5}
        mock_boto3_client.return_value = mock_client

        manager = ParameterManager()
        model = Parameter(
            Name="/grafana/hub/provisioning-token",
            Value="new-value",
            Type="SecureString",
        )
        manager.update(model, Overwrite=True)

        mock_client.add_tags_to_resource.assert_not_called()
