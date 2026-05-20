from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import (
    AssociateNatGatewayAddressResult,
    ModifyVpcPeeringConnectionOptionsResult,
    NatGatewayManager,
    PeeringConnectionOptionsRequest,
    VpcPeeringConnectionManager,
    VpnConnection,
    VpnConnectionManager,
)


class TestNatGatewayManagerAddressOps:
    @patch("boto3.client")
    def test_associate_address_wires_nat_gateway_and_allocation_ids(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.associate_nat_gateway_address.return_value = {
            "NatGatewayId": "nat-123",
            "NatGatewayAddresses": [{"AllocationId": "eipalloc-123"}],
        }
        mock_boto3_client.return_value = mock_client

        manager = NatGatewayManager()
        result = manager.associate_address("nat-123", ["eipalloc-123"])

        mock_client.associate_nat_gateway_address.assert_called_once_with(
            NatGatewayId="nat-123",
            AllocationIds=["eipalloc-123"],
            DryRun=False,
        )
        assert isinstance(result, AssociateNatGatewayAddressResult)
        assert result.NatGatewayId == "nat-123"

    @patch("boto3.client")
    def test_disassociate_address_wires_nat_gateway_and_association_ids(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.disassociate_nat_gateway_address.return_value = {
            "NatGatewayId": "nat-123",
            "NatGatewayAddresses": [],
        }
        mock_boto3_client.return_value = mock_client

        manager = NatGatewayManager()
        manager.disassociate_address("nat-123", ["assoc-123"])

        mock_client.disassociate_nat_gateway_address.assert_called_once_with(
            NatGatewayId="nat-123",
            AssociationIds=["assoc-123"],
            DryRun=False,
        )


class TestVpcPeeringConnectionManagerModifyOptions:
    @patch("boto3.client")
    def test_modify_options_wires_requester_allow_dns(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.modify_vpc_peering_connection_options.return_value = {
            "RequesterPeeringConnectionOptions": {
                "AllowDnsResolutionFromRemoteVpc": True,
            },
        }
        mock_boto3_client.return_value = mock_client

        manager = VpcPeeringConnectionManager()
        result = manager.modify_options(
            "pcx-123",
            RequesterPeeringConnectionOptions=PeeringConnectionOptionsRequest(
                AllowDnsResolutionFromRemoteVpc=True,
            ),
        )

        mock_client.modify_vpc_peering_connection_options.assert_called_once_with(
            VpcPeeringConnectionId="pcx-123",
            RequesterPeeringConnectionOptions={
                "AllowDnsResolutionFromRemoteVpc": True,
            },
            DryRun=False,
        )
        assert isinstance(result, ModifyVpcPeeringConnectionOptionsResult)
        assert result.RequesterPeeringConnectionOptions is not None
        assert (
            result.RequesterPeeringConnectionOptions.AllowDnsResolutionFromRemoteVpc
            is True
        )


class TestVpnConnectionManagerModify:
    @patch("boto3.client")
    def test_modify_wires_customer_gateway_id(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.modify_vpn_connection.return_value = {
            "VpnConnection": {
                "VpnConnectionId": "vpn-123",
                "CustomerGatewayId": "cgw-new",
                "State": "available",
            },
        }
        mock_boto3_client.return_value = mock_client

        manager = VpnConnectionManager()
        connection = manager.modify("vpn-123", CustomerGatewayId="cgw-new")

        mock_client.modify_vpn_connection.assert_called_once_with(
            VpnConnectionId="vpn-123",
            CustomerGatewayId="cgw-new",
            DryRun=False,
        )
        assert isinstance(connection, VpnConnection)
        assert connection.VpnConnectionId == "vpn-123"
        assert connection.CustomerGatewayId == "cgw-new"
