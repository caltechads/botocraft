from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import (
    AssociateRouteTableResult,
    IpPermission,
    RouteTableManager,
    SecurityGroupManager,
    VolumeAttachment,
    VolumeManager,
)


class TestVolumeManagerAttachDetach:
    @patch("boto3.client")
    def test_attach_wires_volume_instance_and_device(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.attach_volume.return_value = {
            "VolumeId": "vol-123",
            "InstanceId": "i-123",
            "Device": "/dev/sdf",
            "State": "attaching",
        }
        mock_boto3_client.return_value = mock_client

        manager = VolumeManager()
        attachment = manager.attach(
            Device="/dev/sdf",
            InstanceId="i-123",
            VolumeId="vol-123",
        )

        mock_client.attach_volume.assert_called_once_with(
            Device="/dev/sdf",
            InstanceId="i-123",
            VolumeId="vol-123",
            DryRun=False,
        )
        assert isinstance(attachment, VolumeAttachment)
        assert attachment.VolumeId == "vol-123"
        assert attachment.State == "attaching"

    @patch("boto3.client")
    def test_detach_wires_volume_id_and_force(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.detach_volume.return_value = {
            "VolumeId": "vol-123",
            "State": "detaching",
        }
        mock_boto3_client.return_value = mock_client

        manager = VolumeManager()
        attachment = manager.detach("vol-123", Force=True)

        mock_client.detach_volume.assert_called_once_with(
            VolumeId="vol-123",
            Force=True,
            DryRun=False,
        )
        assert isinstance(attachment, VolumeAttachment)
        assert attachment.VolumeId == "vol-123"


class TestSecurityGroupManagerEgress:
    @patch("boto3.client")
    def test_authorize_egress_wires_group_and_permissions(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.authorize_security_group_egress.return_value = {"Return": True}
        mock_boto3_client.return_value = mock_client

        permissions = [
            IpPermission(IpProtocol="tcp", FromPort=443, ToPort=443, IpRanges=[]),
        ]
        manager = SecurityGroupManager()
        authorized = manager.authorize_egress("sg-123", permissions)

        mock_client.authorize_security_group_egress.assert_called_once()
        call_kwargs = mock_client.authorize_security_group_egress.call_args.kwargs
        assert call_kwargs["GroupId"] == "sg-123"
        assert call_kwargs["DryRun"] is False
        assert authorized is True

    @patch("boto3.client")
    def test_revoke_egress_wires_group_and_permissions(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.revoke_security_group_egress.return_value = {"Return": True}
        mock_boto3_client.return_value = mock_client

        permissions = [
            IpPermission(IpProtocol="tcp", FromPort=443, ToPort=443, IpRanges=[]),
        ]
        manager = SecurityGroupManager()
        revoked = manager.revoke_egress("sg-123", permissions)

        mock_client.revoke_security_group_egress.assert_called_once()
        call_kwargs = mock_client.revoke_security_group_egress.call_args.kwargs
        assert call_kwargs["GroupId"] == "sg-123"
        assert call_kwargs["DryRun"] is False
        assert call_kwargs["IpPermissions"] == [
            {
                "IpProtocol": "tcp",
                "FromPort": 443,
                "ToPort": 443,
                "UserIdGroupPairs": [],
                "IpRanges": [],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
            }
        ]
        assert revoked is True


class TestRouteTableManagerAssociation:
    @patch("boto3.client")
    def test_associate_wires_subnet_and_route_table(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.associate_route_table.return_value = {
            "AssociationId": "rtbassoc-123",
            "AssociationState": {"State": "associated"},
        }
        mock_boto3_client.return_value = mock_client

        manager = RouteTableManager()
        result = manager.associate("rtb-123", SubnetId="subnet-123")

        mock_client.associate_route_table.assert_called_once_with(
            RouteTableId="rtb-123",
            SubnetId="subnet-123",
            DryRun=False,
        )
        assert isinstance(result, AssociateRouteTableResult)
        assert result.AssociationId == "rtbassoc-123"

    @patch("boto3.client")
    def test_disassociate_wires_association_id(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        manager = RouteTableManager()
        manager.disassociate("rtbassoc-123")

        mock_client.disassociate_route_table.assert_called_once_with(
            AssociationId="rtbassoc-123",
            DryRun=False,
        )
