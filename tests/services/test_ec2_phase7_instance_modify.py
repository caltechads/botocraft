from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import (
    AttributeBooleanValue,
    AttributeValue,
    BlobAttributeValue,
    InstanceManager,
)


class TestInstanceManagerModifyAttributes:
    @patch("boto3.client")
    def test_modify_instance_type_wires_instance_and_type(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = InstanceManager()
        manager.modify_instance_type(
            "i-123",
            InstanceType=AttributeValue(Value="m5.large"),
        )

        mock_client.modify_instance_attribute.assert_called_once_with(
            InstanceId="i-123",
            InstanceType={"Value": "m5.large"},
            DryRun=False,
        )

    @patch("boto3.client")
    def test_modify_source_dest_check_wires_boolean_attribute(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = InstanceManager()
        manager.modify_source_dest_check(
            AttributeBooleanValue(Value=False),
            "i-123",
        )

        mock_client.modify_instance_attribute.assert_called_once_with(
            InstanceId="i-123",
            SourceDestCheck={"Value": False},
            DryRun=False,
        )

    @patch("boto3.client")
    def test_modify_disable_api_termination_wires_boolean_attribute(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = InstanceManager()
        manager.modify_disable_api_termination(
            "i-123",
            DisableApiTermination=AttributeBooleanValue(Value=True),
        )

        mock_client.modify_instance_attribute.assert_called_once_with(
            InstanceId="i-123",
            DisableApiTermination={"Value": True},
            DryRun=False,
        )

    @patch("boto3.client")
    def test_modify_ebs_optimized_wires_boolean_attribute(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = InstanceManager()
        manager.modify_ebs_optimized(
            "i-123",
            EbsOptimized=AttributeBooleanValue(Value=True),
        )

        mock_client.modify_instance_attribute.assert_called_once_with(
            InstanceId="i-123",
            EbsOptimized={"Value": True},
            DryRun=False,
        )

    @patch("boto3.client")
    def test_modify_user_data_wires_blob_attribute(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = InstanceManager()
        manager.modify_user_data(
            "i-123",
            UserData=BlobAttributeValue(Value="dGVzdA=="),
        )

        mock_client.modify_instance_attribute.assert_called_once_with(
            InstanceId="i-123",
            UserData={"Value": b"dGVzdA=="},
            DryRun=False,
        )
