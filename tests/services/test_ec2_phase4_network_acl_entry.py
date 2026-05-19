from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import NetworkAclManager


class TestNetworkAclManagerEntries:
    @patch("boto3.client")
    def test_create_entry_wires_required_fields_and_cidr(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = NetworkAclManager()
        manager.create_entry(
            "acl-123",
            RuleNumber=100,
            Protocol="-1",
            RuleAction="allow",
            Egress=False,
            CidrBlock="0.0.0.0/0",
        )

        mock_client.create_network_acl_entry.assert_called_once_with(
            NetworkAclId="acl-123",
            RuleNumber=100,
            Protocol="-1",
            RuleAction="allow",
            Egress=False,
            CidrBlock="0.0.0.0/0",
            DryRun=False,
        )

    @patch("boto3.client")
    def test_replace_entry_wires_egress_rule(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = NetworkAclManager()
        manager.replace_entry(
            "acl-123",
            RuleNumber=200,
            Protocol="6",
            RuleAction="deny",
            Egress=True,
            CidrBlock="10.0.0.0/16",
        )

        mock_client.replace_network_acl_entry.assert_called_once_with(
            NetworkAclId="acl-123",
            RuleNumber=200,
            Protocol="6",
            RuleAction="deny",
            Egress=True,
            CidrBlock="10.0.0.0/16",
            DryRun=False,
        )

    @patch("boto3.client")
    def test_delete_entry_wires_rule_number_and_egress(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = NetworkAclManager()
        manager.delete_entry("acl-123", RuleNumber=100, Egress=False)

        mock_client.delete_network_acl_entry.assert_called_once_with(
            NetworkAclId="acl-123",
            RuleNumber=100,
            Egress=False,
            DryRun=False,
        )
