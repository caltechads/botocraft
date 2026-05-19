from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import (
    AssignPrivateIpAddressesResult,
    AttributeBooleanValue,
    AttributeValue,
    NetworkInterfaceManager,
)


class TestNetworkInterfaceManagerPrivateIpsAndModify:
    @patch("boto3.client")
    def test_assign_private_ips_wires_interface_and_addresses(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.assign_private_ip_addresses.return_value = {
            "NetworkInterfaceId": "eni-123",
            "AssignedPrivateIpAddresses": [
                {"PrivateIpAddress": "10.0.1.10", "Primary": False},
            ],
        }
        mock_boto3_client.return_value = mock_client

        manager = NetworkInterfaceManager()
        result = manager.assign_private_ips(
            "eni-123",
            PrivateIpAddresses=["10.0.1.10"],
        )

        mock_client.assign_private_ip_addresses.assert_called_once_with(
            NetworkInterfaceId="eni-123",
            PrivateIpAddresses=["10.0.1.10"],
        )
        assert isinstance(result, AssignPrivateIpAddressesResult)
        assert result.NetworkInterfaceId == "eni-123"
        assert result.AssignedPrivateIpAddresses is not None
        assert result.AssignedPrivateIpAddresses[0].PrivateIpAddress == "10.0.1.10"

    @patch("boto3.client")
    def test_unassign_private_ips_wires_interface_and_addresses(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = NetworkInterfaceManager()
        manager.unassign_private_ips(
            "eni-123",
            PrivateIpAddresses=["10.0.1.10"],
        )

        mock_client.unassign_private_ip_addresses.assert_called_once_with(
            NetworkInterfaceId="eni-123",
            PrivateIpAddresses=["10.0.1.10"],
        )

    @patch("boto3.client")
    def test_modify_wires_description_attribute(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = NetworkInterfaceManager()
        manager.modify(
            "eni-123",
            Description=AttributeValue(Value="edge"),
            DryRun=False,
        )

        mock_client.modify_network_interface_attribute.assert_called_once_with(
            NetworkInterfaceId="eni-123",
            Description={"Value": "edge"},
            DryRun=False,
        )

    @patch("boto3.client")
    def test_modify_wires_source_dest_check(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = NetworkInterfaceManager()
        manager.modify(
            "eni-123",
            SourceDestCheck=AttributeBooleanValue(Value=False),
        )

        mock_client.modify_network_interface_attribute.assert_called_once_with(
            NetworkInterfaceId="eni-123",
            DryRun=False,
            SourceDestCheck={"Value": False},
        )
