from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import SnapshotManager, Volume, VolumeManager


class TestVolumeManagerCreateFromSnapshot:
    @patch("boto3.client")
    def test_create_from_snapshot_passes_size_and_zone(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_volume.return_value = {
            "VolumeId": "vol-new",
            "SnapshotId": "snap-src",
            "AvailabilityZone": "us-west-2a",
            "Size": 100,
            "State": "creating",
        }
        mock_boto3_client.return_value = mock_client

        manager = VolumeManager()
        volume = manager.create(
            Volume(
                SnapshotId="snap-src",
                AvailabilityZone="us-west-2a",
                Size=100,
                VolumeType="gp3",
            )
        )

        mock_client.create_volume.assert_called_once()
        assert mock_client.create_volume.call_args.kwargs == {
            "SnapshotId": "snap-src",
            "AvailabilityZone": "us-west-2a",
            "Size": 100,
            "VolumeType": "gp3",
            "TagSpecifications": {"ResourceType": "volume", "Tags": []},
        }
        assert volume.VolumeId == "vol-new"


class TestSnapshotManagerCopyAndUnlock:
    @patch("boto3.client")
    def test_copy_wires_source_region_and_snapshot_id(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.copy_snapshot.return_value = {"SnapshotId": "snap-copy"}
        mock_boto3_client.return_value = mock_client

        manager = SnapshotManager()
        snapshot_id = manager.copy("us-east-1", "snap-src")

        mock_client.copy_snapshot.assert_called_once_with(
            SourceRegion="us-east-1",
            SourceSnapshotId="snap-src",
            DryRun=False,
        )
        assert snapshot_id == "snap-copy"

    @patch("boto3.client")
    def test_unlock_wires_snapshot_id(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.unlock_snapshot.return_value = {"SnapshotId": "snap-123"}
        mock_boto3_client.return_value = mock_client

        manager = SnapshotManager()
        snapshot_id = manager.unlock("snap-123")

        mock_client.unlock_snapshot.assert_called_once_with(
            SnapshotId="snap-123",
            DryRun=False,
        )
        assert snapshot_id == "snap-123"
