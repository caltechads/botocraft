from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.common import Tag
from botocraft.services.ec2 import (
    CustomerGateway,
    CustomerGatewayManager,
    EC2VpcAttachment,
    EC2VpcEndpoint,
    EC2VpcEndpointManager,
    FlowLog,
    FlowLogManager,
    ImportKeyPairResult,
    InternetGatewayManager,
    KeyPair,
    KeyPairManager,
    VpcPeeringConnection,
    VpcPeeringConnectionManager,
    VpnGatewayManager,
)


class FakePaginator:
    """Minimal paginator stub matching boto3 paginator protocol."""

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses

    def paginate(self, **_: object) -> list[dict[str, object]]:
        return self.responses


class TestKeyPairManager:
    @patch("boto3.client")
    def test_create_get_delete_wire_requests_and_responses(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_key_pair.return_value = {
            "KeyPairId": "key-123",
            "KeyName": "demo",
            "KeyFingerprint": "aa:bb",
            "KeyMaterial": "PRIVATE KEY",
            "Tags": [{"Key": "Name", "Value": "demo"}],
        }
        mock_client.describe_key_pairs.return_value = {
            "KeyPairs": [
                {
                    "KeyPairId": "key-123",
                    "KeyName": "demo",
                    "KeyFingerprint": "aa:bb",
                    "KeyType": "rsa",
                    "PublicKey": "ssh-rsa AAAA",
                    "CreateTime": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "Tags": [{"Key": "Name", "Value": "demo"}],
                }
            ]
        }
        mock_client.delete_key_pair.return_value = {
            "Return": True,
            "KeyPairId": "key-123",
        }
        mock_boto3_client.return_value = mock_client

        manager = KeyPairManager()
        model = KeyPair(
            KeyName="demo",
            Tags=[Tag(Key="Name", Value="demo")],
        )

        created = manager.create(model)
        loaded = manager.get("key-123")
        deleted = manager.delete("key-123")

        mock_client.create_key_pair.assert_called_once_with(
            KeyName="demo",
            TagSpecifications={
                "ResourceType": "key-pair",
                "Tags": [{"Key": "Name", "Value": "demo"}],
            },
        )
        mock_client.describe_key_pairs.assert_called_once_with(
            KeyPairIds=["key-123"],
            IncludePublicKey=True,
            DryRun=False,
        )
        mock_client.delete_key_pair.assert_called_once_with(
            KeyPairId="key-123",
            DryRun=False,
        )
        assert isinstance(created, KeyPair)
        assert created.KeyMaterial == "PRIVATE KEY"
        assert loaded is not None
        assert loaded.__class__.__name__ == "KeyPairInfo"
        assert loaded.KeyPairId == "key-123"
        assert loaded.PublicKey == "ssh-rsa AAAA"
        assert deleted.KeyPairId == "key-123"

    @patch("boto3.client")
    def test_import_key_pair_wires_public_key_and_tags(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.import_key_pair.return_value = {
            "KeyPairId": "key-imported",
            "KeyName": "imported",
            "KeyFingerprint": "aa:bb",
            "Tags": [{"Key": "Name", "Value": "imported"}],
        }
        mock_boto3_client.return_value = mock_client

        manager = KeyPairManager()
        imported = manager.import_key_pair(
            "imported",
            b"ssh-rsa AAAA",
            Tags=[Tag(Key="Name", Value="imported")],
        )

        mock_client.import_key_pair.assert_called_once_with(
            KeyName="imported",
            PublicKeyMaterial=b"ssh-rsa AAAA",
            TagSpecifications={
                "ResourceType": "key-pair",
                "Tags": [{"Key": "Name", "Value": "imported"}],
            },
            DryRun=False,
        )
        assert isinstance(imported, ImportKeyPairResult)
        assert imported.KeyPairId == "key-imported"


class TestFlowLogManager:
    @patch("boto3.client")
    def test_get_and_list_shape_flow_log_models(
        self, mock_boto3_client: MagicMock
    ) -> None:
        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_client = MagicMock()
        mock_client.describe_flow_logs.return_value = {
            "FlowLogs": [
                {
                    "FlowLogId": "fl-123",
                    "ResourceId": "vpc-123",
                    "ResourceType": "VPC",
                    "TrafficType": "ALL",
                    "LogDestinationType": "cloud-watch-logs",
                    "CreationTime": created_at,
                }
            ]
        }
        mock_client.get_paginator.return_value = FakePaginator(
            [
                {
                    "FlowLogs": [
                        {
                            "FlowLogId": "fl-123",
                            "ResourceId": "vpc-123",
                            "ResourceType": "VPC",
                            "TrafficType": "ALL",
                            "LogDestinationType": "cloud-watch-logs",
                            "CreationTime": created_at,
                        }
                    ]
                }
            ]
        )
        mock_boto3_client.return_value = mock_client

        manager = FlowLogManager()
        loaded = manager.get("fl-123")
        flow_logs = manager.list()

        mock_client.describe_flow_logs.assert_called_once_with(
            FlowLogIds=["fl-123"],
            DryRun=False,
        )
        mock_client.get_paginator.assert_called_once_with("describe_flow_logs")
        assert isinstance(loaded, FlowLog)
        assert loaded.FlowLogId == "fl-123"
        assert isinstance(flow_logs, PrimaryBoto3ModelQuerySet)
        assert len(flow_logs) == 1
        assert isinstance(flow_logs[0], FlowLog)


class TestEC2VpcEndpointManager:
    @patch("boto3.client")
    def test_public_class_name_avoids_collision_and_manager_round_trips(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_vpc_endpoint.return_value = {
            "VpcEndpoint": {
                "VpcEndpointId": "vpce-123",
                "VpcId": "vpc-123",
                "ServiceName": "com.amazonaws.us-west-2.s3",
                "VpcEndpointType": "Gateway",
            }
        }
        mock_client.describe_vpc_endpoints.return_value = {
            "VpcEndpoints": [
                {
                    "VpcEndpointId": "vpce-123",
                    "VpcId": "vpc-123",
                    "ServiceName": "com.amazonaws.us-west-2.s3",
                    "VpcEndpointType": "Gateway",
                }
            ]
        }
        mock_client.delete_vpc_endpoints.return_value = {
            "Unsuccessful": [],
        }
        mock_boto3_client.return_value = mock_client

        manager = EC2VpcEndpointManager()
        model = EC2VpcEndpoint(
            VpcId="vpc-123",
            ServiceName="com.amazonaws.us-west-2.s3",
            VpcEndpointType="Gateway",
        )

        created = manager.create(model)
        loaded = manager.get("vpce-123")
        manager.delete("vpce-123")

        assert isinstance(created, EC2VpcEndpoint)
        assert isinstance(loaded, EC2VpcEndpoint)
        mock_client.describe_vpc_endpoints.assert_called_once_with(
            VpcEndpointIds=["vpce-123"],
            DryRun=False,
        )


class TestCustomerGatewayManager:
    @patch("boto3.client")
    def test_create_get_list_delete_wire_wrapper_resource(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_customer_gateway.return_value = {
            "CustomerGateway": {
                "CustomerGatewayId": "cgw-123",
                "IpAddress": "203.0.113.10",
                "BgpAsn": 65000,
                "Type": "ipsec.1",
            }
        }
        mock_client.describe_customer_gateways.return_value = {
            "CustomerGateways": [
                {
                    "CustomerGatewayId": "cgw-123",
                    "IpAddress": "203.0.113.10",
                    "BgpAsn": 65000,
                    "Type": "ipsec.1",
                }
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = CustomerGatewayManager()
        model = CustomerGateway(
            IpAddress="203.0.113.10",
            BgpAsn=65000,
            Type="ipsec.1",
            Tags=None,
        )

        created = manager.create(model)
        loaded = manager.get("cgw-123")
        gateways = manager.list()
        manager.delete("cgw-123")

        assert isinstance(created, CustomerGateway)
        assert isinstance(loaded, CustomerGateway)
        assert isinstance(gateways, PrimaryBoto3ModelQuerySet)
        assert len(gateways) == 1
        mock_client.create_customer_gateway.assert_called_once_with(
            Type="ipsec.1",
            BgpAsn=65000,
            PublicIp="203.0.113.10",
        )
        assert mock_client.describe_customer_gateways.call_args_list == [
            (
                (),
                {"CustomerGatewayIds": ["cgw-123"], "DryRun": False},
            ),
            (
                (),
                {"DryRun": False},
            ),
        ]
        mock_client.delete_customer_gateway.assert_called_once_with(
            CustomerGatewayId="cgw-123",
            DryRun=False,
        )


class TestInternetGatewayManager:
    @patch("boto3.client")
    def test_attach_and_detach_wire_vpc_and_gateway_ids(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = InternetGatewayManager()
        manager.attach("igw-123", "vpc-123")
        manager.detach("igw-123", "vpc-123")

        mock_client.attach_internet_gateway.assert_called_once_with(
            InternetGatewayId="igw-123",
            VpcId="vpc-123",
            DryRun=False,
        )
        mock_client.detach_internet_gateway.assert_called_once_with(
            InternetGatewayId="igw-123",
            VpcId="vpc-123",
            DryRun=False,
        )


class TestVpnGatewayManager:
    @patch("boto3.client")
    def test_attach_returns_vpc_attachment(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.attach_vpn_gateway.return_value = {
            "VpcAttachment": {
                "VpcId": "vpc-123",
                "State": "attaching",
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = VpnGatewayManager()
        attachment = manager.attach("vpc-123", "vgw-123")

        mock_client.attach_vpn_gateway.assert_called_once_with(
            VpcId="vpc-123",
            VpnGatewayId="vgw-123",
            DryRun=False,
        )
        assert isinstance(attachment, EC2VpcAttachment)
        assert attachment.VpcId == "vpc-123"
        assert attachment.State == "attaching"

    @patch("boto3.client")
    def test_detach_wires_vpc_and_gateway_ids(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = VpnGatewayManager()
        manager.detach("vpc-123", "vgw-123")

        mock_client.detach_vpn_gateway.assert_called_once_with(
            VpcId="vpc-123",
            VpnGatewayId="vgw-123",
            DryRun=False,
        )


class TestVpcPeeringConnectionManager:
    @patch("boto3.client")
    def test_accept_and_reject_wire_peering_connection_id(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.accept_vpc_peering_connection.return_value = {
            "VpcPeeringConnection": {
                "VpcPeeringConnectionId": "pcx-123",
                "Status": {"Code": "active"},
            }
        }
        mock_client.reject_vpc_peering_connection.return_value = {"Return": True}
        mock_boto3_client.return_value = mock_client

        manager = VpcPeeringConnectionManager()
        accepted = manager.accept("pcx-123")
        rejected = manager.reject("pcx-123")

        mock_client.accept_vpc_peering_connection.assert_called_once_with(
            VpcPeeringConnectionId="pcx-123",
            DryRun=False,
        )
        mock_client.reject_vpc_peering_connection.assert_called_once_with(
            VpcPeeringConnectionId="pcx-123",
            DryRun=False,
        )
        assert isinstance(accepted, VpcPeeringConnection)
        assert accepted.VpcPeeringConnectionId == "pcx-123"
        assert rejected is True
