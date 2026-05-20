from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import (
    DeleteVpcEndpointsResult,
    EC2VpcEndpointManager,
    Volume,
    VolumeManager,
)


class TestEC2VpcEndpointManagerDelete:
    @patch("boto3.client")
    def test_delete_returns_delete_vpc_endpoints_result(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.delete_vpc_endpoints.return_value = {
            "Unsuccessful": [{"Error": {"Code": "InvalidVpcEndpointId.NotFound"}}],
        }
        mock_boto3_client.return_value = mock_client

        manager = EC2VpcEndpointManager()
        result = manager.delete("vpce-123")

        mock_client.delete_vpc_endpoints.assert_called_once_with(
            VpcEndpointIds=["vpce-123"],
            DryRun=False,
        )
        assert isinstance(result, DeleteVpcEndpointsResult)
        assert result.Unsuccessful is not None
        assert len(result.Unsuccessful) == 1


class TestVolumeManagerCreateFromSnapshot:
    @patch("boto3.client")
    def test_create_wires_snapshot_id_and_availability_zone(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_volume.return_value = {
            "VolumeId": "vol-123",
            "SnapshotId": "snap-123",
            "AvailabilityZone": "us-east-1a",
            "Size": 8,
            "State": "creating",
        }
        mock_boto3_client.return_value = mock_client

        manager = VolumeManager()
        volume = manager.create(
            Volume(
                SnapshotId="snap-123",
                AvailabilityZone="us-east-1a",
                Size=8,
            )
        )

        mock_client.create_volume.assert_called_once()
        assert mock_client.create_volume.call_args.kwargs == {
            "SnapshotId": "snap-123",
            "AvailabilityZone": "us-east-1a",
            "Size": 8,
            "TagSpecifications": {"ResourceType": "volume", "Tags": []},
        }
        assert volume.VolumeId == "vol-123"
        assert volume.SnapshotId == "snap-123"
