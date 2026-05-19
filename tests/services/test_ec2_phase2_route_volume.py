from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import (
    EC2VolumeModification,
    RouteTableManager,
    Volume,
    VolumeManager,
)


class TestRouteTableManagerRoutes:
    @patch("boto3.client")
    def test_create_route_wires_destination_and_target(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_route.return_value = {"Return": True}
        mock_boto3_client.return_value = mock_client

        manager = RouteTableManager()
        created = manager.create_route(
            "rtb-123",
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId="igw-123",
        )

        mock_client.create_route.assert_called_once_with(
            RouteTableId="rtb-123",
            DestinationCidrBlock="0.0.0.0/0",
            GatewayId="igw-123",
            DryRun=False,
        )
        assert created is True

    @patch("boto3.client")
    def test_delete_route_wires_route_table_and_destination(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = RouteTableManager()
        manager.delete_route(
            "rtb-123",
            DestinationCidrBlock="10.0.0.0/16",
        )

        mock_client.delete_route.assert_called_once_with(
            RouteTableId="rtb-123",
            DestinationCidrBlock="10.0.0.0/16",
            DryRun=False,
        )

    @patch("boto3.client")
    def test_replace_route_wires_nat_gateway_target(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = RouteTableManager()
        manager.replace_route(
            "rtb-123",
            DestinationCidrBlock="0.0.0.0/0",
            NatGatewayId="nat-123",
        )

        mock_client.replace_route.assert_called_once_with(
            RouteTableId="rtb-123",
            DestinationCidrBlock="0.0.0.0/0",
            NatGatewayId="nat-123",
            DryRun=False,
        )


class TestVolumeManagerUpdate:
    @patch("boto3.client")
    def test_update_wires_modify_volume_from_model(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.modify_volume.return_value = {
            "VolumeModification": {
                "VolumeId": "vol-123",
                "ModificationState": "modifying",
                "TargetSize": 100,
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = VolumeManager()
        modification = manager.update(
            Volume(VolumeId="vol-123", Size=100, VolumeType="gp3")
        )

        mock_client.modify_volume.assert_called_once_with(
            VolumeId="vol-123",
            Size=100,
            VolumeType="gp3",
        )
        assert isinstance(modification, EC2VolumeModification)
        assert modification.VolumeId == "vol-123"
        assert modification.TargetSize == 100
