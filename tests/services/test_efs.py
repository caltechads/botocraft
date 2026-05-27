from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.common import Tag
from botocraft.services.ec2 import (
    SecurityGroup,
    SecurityGroupManager,
    Subnet,
    SubnetManager,
    Vpc,
    VpcManager,
)
from botocraft.services.efs import (
    AccessPoint,
    AccessPointManager,
    EFSBackupPolicy,
    FileSystem,
    FileSystemManager,
    FileSystemPolicyDescription,
    FileSystemProtectionDescription,
    LifecycleConfigurationDescription,
    LifecyclePolicy,
    MountTarget,
    MountTargetManager,
    ReplicationConfiguration,
    ReplicationConfigurationManager,
)


class FakePaginator:
    """Minimal paginator stub matching boto3 paginator protocol."""

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses

    def paginate(self, **_: object) -> list[dict[str, object]]:
        return self.responses


def _return_self(_self: object, _session: object) -> object:
    """Return patched manager instance for `.using(...)` helpers."""
    return _self


def _file_system_payload(file_system_id: str = "fs-123") -> dict[str, object]:
    """Return minimal EFS file-system payload."""
    return {
        "OwnerId": "123456789012",
        "CreationToken": "token-123",
        "FileSystemId": file_system_id,
        "FileSystemArn": f"arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/{file_system_id}",
        "CreationTime": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "LifeCycleState": "available",
        "Name": "shared-data",
        "NumberOfMountTargets": 1,
        "SizeInBytes": {
            "Value": 1024,
            "Timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        "PerformanceMode": "generalPurpose",
        "Encrypted": True,
        "KmsKeyId": "alias/aws/elasticfilesystem",
        "ThroughputMode": "bursting",
        "Tags": [{"Key": "Name", "Value": "shared-data"}],
        "FileSystemProtection": {
            "ReplicationOverwriteProtection": "DISABLED",
        },
    }


def _access_point_payload(access_point_id: str = "fsap-123") -> dict[str, object]:
    """Return minimal EFS access-point payload."""
    return {
        "ClientToken": "client-token-123",
        "Name": "app-access",
        "Tags": [{"Key": "Name", "Value": "app-access"}],
        "AccessPointId": access_point_id,
        "AccessPointArn": f"arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/{access_point_id}",
        "FileSystemId": "fs-123",
        "PosixUser": {"Uid": 1000, "Gid": 1000, "SecondaryGids": [1001]},
        "RootDirectory": {
            "Path": "/app",
            "CreationInfo": {
                "OwnerUid": 1000,
                "OwnerGid": 1000,
                "Permissions": "0755",
            },
        },
        "OwnerId": "123456789012",
        "LifeCycleState": "available",
    }


def _mount_target_payload(mount_target_id: str = "fsmt-123") -> dict[str, object]:
    """Return minimal EFS mount-target payload."""
    return {
        "OwnerId": "123456789012",
        "MountTargetId": mount_target_id,
        "FileSystemId": "fs-123",
        "SubnetId": "subnet-123",
        "LifeCycleState": "available",
        "IpAddress": "10.0.0.25",
        "NetworkInterfaceId": "eni-123",
        "AvailabilityZoneId": "usw2-az1",
        "AvailabilityZoneName": "us-west-2a",
        "VpcId": "vpc-123",
    }


def _replication_payload(source_file_system_id: str = "fs-123") -> dict[str, object]:
    """Return minimal EFS replication payload."""
    return {
        "SourceFileSystemId": source_file_system_id,
        "SourceFileSystemRegion": "us-west-2",
        "SourceFileSystemArn": f"arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/{source_file_system_id}",
        "OriginalSourceFileSystemArn": f"arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/{source_file_system_id}",
        "CreationTime": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "Destinations": [
            {
                "Status": "ENABLED",
                "FileSystemId": "fs-dest-123",
                "Region": "us-east-1",
                "LastReplicatedTimestamp": datetime(2024, 1, 2, tzinfo=timezone.utc),
                "OwnerId": "123456789012",
                "StatusMessage": "healthy",
                "RoleArn": "arn:aws:iam::123456789012:role/efs-replication",
            }
        ],
        "SourceFileSystemOwnerId": "123456789012",
    }


class TestFileSystemManager:
    @patch("boto3.client")
    def test_crud_and_tag_hydration(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_file_system.return_value = _file_system_payload()
        mock_client.describe_file_systems.return_value = {
            "FileSystems": [_file_system_payload()]
        }
        mock_client.delete_file_system.return_value = {}
        mock_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Name", "Value": "shared-data"}]
        }
        mock_client.get_paginator.return_value = FakePaginator(
            [{"FileSystems": [_file_system_payload()]}]
        )
        mock_boto3_client.return_value = mock_client

        manager = FileSystemManager()
        model = FileSystem(
            CreationToken="token-123",
            PerformanceMode="generalPurpose",
            Tags=[Tag(Key="Name", Value="shared-data")],
        )

        created = manager.create(model)
        loaded = manager.get("fs-123")
        file_systems = manager.list(FileSystemId="fs-123")
        manager.delete("fs-123")

        mock_client.create_file_system.assert_called_once_with(
            CreationToken="token-123",
            PerformanceMode="generalPurpose",
            Tags=[{"Key": "Name", "Value": "shared-data"}],
        )
        mock_client.describe_file_systems.assert_called_once_with(FileSystemId="fs-123")
        mock_client.delete_file_system.assert_called_once_with(FileSystemId="fs-123")
        mock_client.get_paginator.assert_called_once_with("describe_file_systems")
        assert mock_client.list_tags_for_resource.call_count == 3
        assert isinstance(created, FileSystem)
        assert isinstance(loaded, FileSystem)
        assert isinstance(file_systems, PrimaryBoto3ModelQuerySet)
        assert created.Tags is not None
        assert loaded.Tags is not None
        assert file_systems[0].Tags is not None
        assert loaded.tags["Name"] == "shared-data"

    @patch("boto3.client")
    def test_file_system_scoped_helpers(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.describe_backup_policy.return_value = {
            "BackupPolicy": {"Status": "ENABLED"}
        }
        mock_client.put_backup_policy.return_value = {
            "BackupPolicy": {"Status": "ENABLED"}
        }
        mock_client.describe_file_system_policy.return_value = {
            "FileSystemId": "fs-123",
            "Policy": '{"Version":"2012-10-17"}',
        }
        mock_client.put_file_system_policy.return_value = {
            "FileSystemId": "fs-123",
            "Policy": '{"Version":"2012-10-17"}',
        }
        mock_client.delete_file_system_policy.return_value = {}
        mock_client.describe_lifecycle_configuration.return_value = {
            "LifecyclePolicies": [
                {"TransitionToIA": "AFTER_30_DAYS"},
            ]
        }
        mock_client.put_lifecycle_configuration.return_value = {
            "LifecyclePolicies": [
                {"TransitionToIA": "AFTER_30_DAYS"},
            ]
        }
        mock_client.describe_file_systems.return_value = {
            "FileSystems": [_file_system_payload()]
        }
        mock_client.update_file_system_protection.return_value = {
            "ReplicationOverwriteProtection": "ENABLED"
        }
        mock_boto3_client.return_value = mock_client

        manager = FileSystemManager()

        backup_policy = manager.get_backup_policy("fs-123")
        updated_backup_policy = manager.put_backup_policy(
            "fs-123",
            EFSBackupPolicy(Status="ENABLED"),
        )
        policy = manager.get_file_system_policy("fs-123")
        updated_policy = manager.put_file_system_policy(
            "fs-123",
            '{"Version":"2012-10-17"}',
        )
        manager.delete_file_system_policy("fs-123")
        lifecycle = manager.get_lifecycle_configuration("fs-123")
        updated_lifecycle = manager.put_lifecycle_configuration(
            "fs-123",
            [LifecyclePolicy(TransitionToIA="AFTER_30_DAYS")],
        )
        protection = manager.update_file_system_protection(
            "fs-123",
            ReplicationOverwriteProtection="ENABLED",
        )

        mock_client.describe_backup_policy.assert_called_once_with(FileSystemId="fs-123")
        mock_client.put_backup_policy.assert_called_once()
        mock_client.describe_file_system_policy.assert_called_once_with(
            FileSystemId="fs-123"
        )
        mock_client.put_file_system_policy.assert_called_once()
        mock_client.delete_file_system_policy.assert_called_once_with(
            FileSystemId="fs-123"
        )
        mock_client.describe_lifecycle_configuration.assert_called_once_with(
            FileSystemId="fs-123"
        )
        mock_client.put_lifecycle_configuration.assert_called_once()
        mock_client.update_file_system_protection.assert_called_once_with(
            FileSystemId="fs-123",
            ReplicationOverwriteProtection="ENABLED",
        )
        assert backup_policy is not None
        assert backup_policy.BackupPolicy is not None
        assert backup_policy.BackupPolicy.Status == "ENABLED"
        assert updated_backup_policy is not None
        assert updated_backup_policy.BackupPolicy is not None
        assert updated_backup_policy.BackupPolicy.Status == "ENABLED"
        assert isinstance(policy, FileSystemPolicyDescription)
        assert isinstance(updated_policy, FileSystemPolicyDescription)
        assert isinstance(lifecycle, LifecycleConfigurationDescription)
        assert isinstance(updated_lifecycle, LifecycleConfigurationDescription)
        assert isinstance(protection, FileSystemProtectionDescription)
        assert protection.ReplicationOverwriteProtection == "ENABLED"

    @patch("boto3.client")
    def test_update_syncs_tags_when_supplied(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.update_file_system.return_value = _file_system_payload()
        mock_client.describe_file_systems.return_value = {
            "FileSystems": [_file_system_payload()]
        }
        mock_client.list_tags_for_resource.side_effect = [
            {
                "Tags": [
                    {"Key": "Name", "Value": "old-name"},
                    {"Key": "Environment", "Value": "test"},
                ]
            },
            {
                "Tags": [
                    {"Key": "Name", "Value": "shared-data"},
                    {"Key": "CostCenter", "Value": "ml"},
                ]
            },
        ]
        mock_client.tag_resource.return_value = {}
        mock_client.untag_resource.return_value = {}
        mock_boto3_client.return_value = mock_client

        manager = FileSystemManager()
        updated = manager.update(
            FileSystem(
                FileSystemId="fs-123",
                ThroughputMode="elastic",
                Tags=[
                    Tag(Key="Name", Value="shared-data"),
                    Tag(Key="CostCenter", Value="ml"),
                ],
            )
        )

        mock_client.update_file_system.assert_called_once_with(
            FileSystemId="fs-123",
            ThroughputMode="elastic",
        )
        mock_client.untag_resource.assert_called_once_with(
            ResourceId="fs-123",
            TagKeys=["Environment"],
        )
        mock_client.tag_resource.assert_called_once_with(
            ResourceId="fs-123",
            Tags=[
                {"Key": "Name", "Value": "shared-data"},
                {"Key": "CostCenter", "Value": "ml"},
            ],
        )
        assert isinstance(updated, FileSystem)
        assert updated.Tags is not None
        assert updated.tags["Name"] == "shared-data"

    def test_relations_and_replication_shortcuts(self) -> None:
        file_system = FileSystem.model_construct(FileSystemId="fs-123", session=None)
        with (
            patch.object(
                AccessPointManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                AccessPointManager,
                "list",
                autospec=True,
                return_value=[AccessPoint.model_construct(AccessPointId="fsap-123")],
            ) as mock_access_point_list,
            patch.object(
                MountTargetManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                MountTargetManager,
                "list",
                autospec=True,
                return_value=[MountTarget.model_construct(MountTargetId="fsmt-123")],
            ) as mock_mount_target_list,
            patch.object(
                ReplicationConfigurationManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                ReplicationConfigurationManager,
                "get",
                autospec=True,
                return_value=ReplicationConfiguration.model_construct(
                    SourceFileSystemId="fs-123"
                ),
            ) as mock_replication_get,
        ):
            access_points = file_system.access_points
            mount_targets = file_system.mount_targets
            replication_configuration = file_system.replication_configuration

        mock_access_point_list.assert_called_once()
        assert mock_access_point_list.call_args.kwargs == {"FileSystemId": "fs-123"}
        mock_mount_target_list.assert_called_once()
        assert mock_mount_target_list.call_args.kwargs == {"FileSystemId": "fs-123"}
        mock_replication_get.assert_called_once()
        assert mock_replication_get.call_args.kwargs == {"SourceFileSystemId": "fs-123"}
        assert access_points[0].AccessPointId == "fsap-123"
        assert mount_targets[0].MountTargetId == "fsmt-123"
        assert replication_configuration is not None
        assert replication_configuration.SourceFileSystemId == "fs-123"


class TestAccessPointManager:
    @patch("boto3.client")
    def test_crud_and_tag_hydration(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_access_point.return_value = _access_point_payload()
        mock_client.describe_access_points.return_value = {
            "AccessPoints": [_access_point_payload()]
        }
        mock_client.delete_access_point.return_value = {}
        mock_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Name", "Value": "app-access"}]
        }
        mock_client.get_paginator.return_value = FakePaginator(
            [{"AccessPoints": [_access_point_payload()]}]
        )
        mock_boto3_client.return_value = mock_client

        manager = AccessPointManager()
        model = AccessPoint(
            ClientToken="client-token-123",
            FileSystemId="fs-123",
            PosixUser={"Uid": 1000, "Gid": 1000},
            RootDirectory={"Path": "/app"},
        )

        created = manager.create(model)
        loaded = manager.get("fsap-123")
        access_points = manager.list(FileSystemId="fs-123")
        manager.delete("fsap-123")

        mock_client.create_access_point.assert_called_once()
        mock_client.describe_access_points.assert_called_once_with(
            AccessPointId="fsap-123"
        )
        mock_client.delete_access_point.assert_called_once_with(
            AccessPointId="fsap-123"
        )
        mock_client.get_paginator.assert_called_once_with("describe_access_points")
        assert mock_client.list_tags_for_resource.call_count == 3
        assert isinstance(created, AccessPoint)
        assert isinstance(loaded, AccessPoint)
        assert isinstance(access_points, PrimaryBoto3ModelQuerySet)
        assert created.Tags is not None
        assert loaded.Tags is not None
        assert access_points[0].Tags is not None
        assert loaded.tags["Name"] == "app-access"

    def test_relations(self) -> None:
        access_point = AccessPoint.model_construct(
            AccessPointId="fsap-123",
            FileSystemId="fs-123",
            session=None,
        )
        with (
            patch.object(
                FileSystemManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                FileSystemManager,
                "get",
                autospec=True,
                return_value=FileSystem.model_construct(FileSystemId="fs-123"),
            ) as mock_file_system_get,
            patch.object(
                MountTargetManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                MountTargetManager,
                "list",
                autospec=True,
                return_value=[MountTarget.model_construct(MountTargetId="fsmt-123")],
            ) as mock_mount_target_list,
        ):
            file_system = access_point.file_system
            mount_targets = access_point.mount_targets

        mock_file_system_get.assert_called_once()
        assert mock_file_system_get.call_args.kwargs == {"FileSystemId": "fs-123"}
        mock_mount_target_list.assert_called_once()
        assert mock_mount_target_list.call_args.kwargs == {"AccessPointId": "fsap-123"}
        assert file_system is not None
        assert file_system.FileSystemId == "fs-123"
        assert mount_targets[0].MountTargetId == "fsmt-123"


class TestMountTargetManager:
    @patch("boto3.client")
    @patch.object(SecurityGroupManager, "using", autospec=True, side_effect=_return_self)
    @patch.object(
        SecurityGroupManager,
        "list",
        autospec=True,
        return_value=[SecurityGroup.model_construct(GroupId="sg-123")],
    )
    def test_crud_and_security_group_helpers(
        self,
        mock_security_group_list: MagicMock,
        mock_security_group_using: MagicMock,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_mount_target.return_value = _mount_target_payload()
        mock_client.describe_mount_targets.return_value = {
            "MountTargets": [_mount_target_payload()]
        }
        mock_client.delete_mount_target.return_value = {}
        mock_client.describe_mount_target_security_groups.return_value = {
            "SecurityGroups": ["sg-123"]
        }
        mock_client.modify_mount_target_security_groups.return_value = {}
        mock_client.get_paginator.return_value = FakePaginator(
            [{"MountTargets": [_mount_target_payload()]}]
        )
        mock_boto3_client.return_value = mock_client

        manager = MountTargetManager()
        model = MountTarget(
            FileSystemId="fs-123",
            SubnetId="subnet-123",
            SecurityGroups=["sg-123"],
        )

        created = manager.create(model)
        loaded = manager.get("fsmt-123")
        mount_targets = manager.list(FileSystemId="fs-123")
        security_groups = manager.get_security_groups("fsmt-123")
        manager.modify_security_groups("fsmt-123", ["sg-123"])
        manager.delete("fsmt-123")

        mock_client.create_mount_target.assert_called_once()
        mock_client.describe_mount_targets.assert_called_once_with(
            MountTargetId="fsmt-123"
        )
        mock_client.describe_mount_target_security_groups.assert_called_once_with(
            MountTargetId="fsmt-123"
        )
        mock_security_group_using.assert_called_once()
        mock_security_group_list.assert_called_once()
        assert mock_security_group_list.call_args.kwargs == {"GroupIds": ["sg-123"]}
        mock_client.modify_mount_target_security_groups.assert_called_once_with(
            MountTargetId="fsmt-123",
            SecurityGroups=["sg-123"],
        )
        mock_client.delete_mount_target.assert_called_once_with(
            MountTargetId="fsmt-123"
        )
        mock_client.get_paginator.assert_called_once_with("describe_mount_targets")
        assert isinstance(created, MountTarget)
        assert isinstance(loaded, MountTarget)
        assert isinstance(mount_targets, PrimaryBoto3ModelQuerySet)
        assert security_groups[0].GroupId == "sg-123"

    def test_relations_and_model_mixin_helpers(self) -> None:
        mount_target = MountTarget.model_construct(
            MountTargetId="fsmt-123",
            FileSystemId="fs-123",
            SubnetId="subnet-123",
            VpcId="vpc-123",
            session=None,
        )
        with (
            patch.object(
                FileSystemManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                FileSystemManager,
                "get",
                autospec=True,
                return_value=FileSystem.model_construct(FileSystemId="fs-123"),
            ) as mock_file_system_get,
            patch.object(
                SecurityGroupManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                SecurityGroupManager,
                "list",
                autospec=True,
                return_value=[SecurityGroup.model_construct(GroupId="sg-123")],
            ),
            patch.object(
                MountTargetManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                MountTargetManager,
                "get_security_groups",
                autospec=True,
                return_value=[SecurityGroup.model_construct(GroupId="sg-123")],
            ) as mock_get_security_groups,
            patch.object(
                MountTargetManager,
                "modify_security_groups",
                autospec=True,
                return_value=None,
            ) as mock_modify_security_groups,
            patch.object(
                SubnetManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                SubnetManager,
                "get",
                autospec=True,
                return_value=Subnet.model_construct(SubnetId="subnet-123"),
            ) as mock_subnet_get,
            patch.object(
                VpcManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                VpcManager,
                "get",
                autospec=True,
                return_value=Vpc.model_construct(VpcId="vpc-123"),
            ) as mock_vpc_get,
        ):
            file_system = mount_target.file_system
            subnet = mount_target.subnet
            vpc = mount_target.vpc
            security_groups = mount_target.security_groups
            updated = mount_target.set_security_groups(["sg-123"])

        mock_file_system_get.assert_called_once()
        assert mock_file_system_get.call_args.kwargs == {"FileSystemId": "fs-123"}
        mock_subnet_get.assert_called_once()
        assert mock_subnet_get.call_args.kwargs == {"SubnetId": "subnet-123"}
        mock_vpc_get.assert_called_once()
        assert mock_vpc_get.call_args.kwargs == {"VpcId": "vpc-123"}
        assert isinstance(subnet, Subnet)
        assert subnet.SubnetId == "subnet-123"
        assert isinstance(vpc, Vpc)
        assert vpc.VpcId == "vpc-123"
        mock_get_security_groups.assert_called_once()
        assert mock_get_security_groups.call_args.args[1] == "fsmt-123"
        mock_modify_security_groups.assert_called_once()
        assert mock_modify_security_groups.call_args.args[1:] == (
            "fsmt-123",
            ["sg-123"],
        )
        assert file_system is not None
        assert file_system.FileSystemId == "fs-123"
        assert security_groups[0].GroupId == "sg-123"
        assert updated is None


class TestReplicationConfigurationManager:
    @patch("boto3.client")
    def test_crud(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_replication_configuration.return_value = _replication_payload()
        mock_client.describe_replication_configurations.return_value = {
            "Replications": [_replication_payload()]
        }
        mock_client.delete_replication_configuration.return_value = {}
        mock_client.get_paginator.return_value = FakePaginator(
            [{"Replications": [_replication_payload()]}]
        )
        mock_boto3_client.return_value = mock_client

        manager = ReplicationConfigurationManager()
        model = ReplicationConfiguration(
            SourceFileSystemId="fs-123",
            Destinations=[
                {
                    "Region": "us-east-1",
                }
            ],
        )

        created = manager.create(model)
        loaded = manager.get("fs-123")
        replications = manager.list()
        manager.delete(
            "fs-123",
            DeletionMode="LOCAL_CONFIGURATION_ONLY",
        )

        mock_client.create_replication_configuration.assert_called_once()
        mock_client.describe_replication_configurations.assert_called_once_with(
            FileSystemId="fs-123"
        )
        mock_client.delete_replication_configuration.assert_called_once_with(
            SourceFileSystemId="fs-123",
            DeletionMode="LOCAL_CONFIGURATION_ONLY",
        )
        mock_client.get_paginator.assert_called_once_with(
            "describe_replication_configurations"
        )
        assert isinstance(created, ReplicationConfiguration)
        assert isinstance(loaded, ReplicationConfiguration)
        assert isinstance(replications, PrimaryBoto3ModelQuerySet)

    def test_relation_to_source_file_system(self) -> None:
        replication = ReplicationConfiguration.model_construct(
            SourceFileSystemId="fs-123",
            session=None,
        )
        with (
            patch.object(
                FileSystemManager,
                "using",
                autospec=True,
                side_effect=_return_self,
            ),
            patch.object(
                FileSystemManager,
                "get",
                autospec=True,
                return_value=FileSystem.model_construct(FileSystemId="fs-123"),
            ) as mock_file_system_get,
        ):
            file_system = replication.source_file_system

        mock_file_system_get.assert_called_once()
        assert mock_file_system_get.call_args.kwargs == {"FileSystemId": "fs-123"}
        assert file_system is not None
        assert file_system.FileSystemId == "fs-123"
