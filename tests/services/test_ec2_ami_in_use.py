from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.autoscaling import AutoScalingGroupManager
from botocraft.services.common import Tag
from botocraft.services.ec2 import (
    AMI,
    AMIManager,
    InstanceManager,
    LaunchTemplateVersion,
    ResponseLaunchTemplateData,
)


def make_ami(image_id: str, environment: str = "test") -> AMI:
    return AMI(
        ImageId=image_id,
        Tags=[Tag(Key="Environment", Value=environment)],
    )


class TestAMIManagerInUse:
    @patch("boto3.client")
    def test_in_use_filters_candidate_amis_by_ami_tags_not_instance_tags(
        self, mock_boto3_client
    ):
        used_ami = make_ami("ami-used")
        unused_ami_1 = make_ami("ami-unused-1")
        unused_ami_2 = make_ami("ami-unused-2")
        candidates = [used_ami, unused_ami_1, unused_ami_2]
        used_instances = PrimaryBoto3ModelQuerySet(
            [SimpleNamespace(ImageId=used_ami.ImageId)]
        )

        mock_boto3_client.return_value = SimpleNamespace()
        manager = AMIManager()

        with (
            patch.object(
                AMIManager,
                "list",
                return_value=PrimaryBoto3ModelQuerySet(candidates),
            ) as mock_ami_list,
            patch.object(
                InstanceManager,
                "list",
                return_value=used_instances,
            ) as mock_instance_list,
            patch.object(
                AutoScalingGroupManager,
                "list",
                return_value=[],
            ),
        ):
            in_use = manager.in_use(tags={"Environment": "test"})

        assert [ami.ImageId for ami in in_use] == [used_ami.ImageId]
        assert in_use[0] is used_ami

        unused_ids = {ami.ImageId for ami in candidates} - {
            ami.ImageId for ami in in_use
        }
        assert unused_ids == {unused_ami_1.ImageId, unused_ami_2.ImageId}

        mock_ami_list.assert_called_once()
        ami_list_kwargs = mock_ami_list.call_args.kwargs
        assert ami_list_kwargs["Owners"] == ["self"]
        assert [f.Name for f in ami_list_kwargs["Filters"]] == ["tag:Environment"]

        mock_instance_list.assert_called_once()
        instance_list_kwargs = mock_instance_list.call_args.kwargs
        assert [f.Name for f in instance_list_kwargs["Filters"]] == ["image-id"]
        assert instance_list_kwargs["Filters"][0].Values == [
            used_ami.ImageId,
            unused_ami_1.ImageId,
            unused_ami_2.ImageId,
        ]

    @patch("boto3.client")
    def test_in_use_filters_candidate_amis_by_ami_tags_not_asg_tags(
        self, mock_boto3_client
    ):
        used_ami = make_ami("ami-used")
        launch_template = LaunchTemplateVersion(
            LaunchTemplateData=ResponseLaunchTemplateData(ImageId=used_ami.ImageId)
        )
        autoscaling_group = SimpleNamespace(
            LaunchConfigurationName=None,
            launch_configuration=None,
            launch_template=launch_template,
        )

        mock_boto3_client.return_value = SimpleNamespace()
        manager = AMIManager()

        with (
            patch.object(
                AMIManager,
                "list",
                return_value=PrimaryBoto3ModelQuerySet([used_ami]),
            ),
            patch.object(
                InstanceManager,
                "list",
                return_value=PrimaryBoto3ModelQuerySet([]),
            ),
            patch.object(
                AutoScalingGroupManager,
                "list",
                return_value=[autoscaling_group],
            ) as mock_asg_list,
        ):
            in_use = manager.in_use(tags={"Environment": "test"})

        assert [ami.ImageId for ami in in_use] == [used_ami.ImageId]
        asg_filters = mock_asg_list.call_args.kwargs.get("Filters") or []
        assert not any(filter_.Name.startswith("tag:") for filter_ in asg_filters)

    @patch("boto3.client")
    def test_in_use_uses_explicit_amis_as_authoritative_candidate_set(
        self, mock_boto3_client
    ):
        used_ami = make_ami("ami-used")
        unused_ami = make_ami("ami-unused")
        explicit_candidates = [used_ami, unused_ami]
        used_instances = PrimaryBoto3ModelQuerySet(
            [SimpleNamespace(ImageId=used_ami.ImageId)]
        )

        mock_boto3_client.return_value = SimpleNamespace()
        manager = AMIManager()

        with (
            patch.object(AMIManager, "list") as mock_ami_list,
            patch.object(
                InstanceManager,
                "list",
                return_value=used_instances,
            ) as mock_instance_list,
            patch.object(
                AutoScalingGroupManager,
                "list",
                return_value=[],
            ),
        ):
            in_use = manager.in_use(
                owners=["amazon"],
                tags={"Environment": "prod"},
                created_since=datetime(2024, 1, 1, tzinfo=timezone.utc),
                amis=explicit_candidates,
            )

        assert [ami.ImageId for ami in in_use] == [used_ami.ImageId]
        mock_ami_list.assert_not_called()

        mock_instance_list.assert_called_once()
        instance_list_kwargs = mock_instance_list.call_args.kwargs
        assert [f.Name for f in instance_list_kwargs["Filters"]] == ["image-id"]
        assert instance_list_kwargs["Filters"][0].Values == [
            used_ami.ImageId,
            unused_ami.ImageId,
        ]

    @patch("boto3.client")
    def test_in_use_detects_asg_launch_configuration_usage(
        self, mock_boto3_client
    ):
        used_ami = make_ami("ami-used")
        launch_configuration = SimpleNamespace(ImageId=used_ami.ImageId)
        autoscaling_group = SimpleNamespace(
            LaunchConfigurationName="lc-used",
            launch_configuration=launch_configuration,
            launch_template=None,
        )

        mock_boto3_client.return_value = SimpleNamespace()
        manager = AMIManager()

        with (
            patch.object(
                AMIManager,
                "list",
                return_value=PrimaryBoto3ModelQuerySet([used_ami]),
            ),
            patch.object(
                InstanceManager,
                "list",
                return_value=PrimaryBoto3ModelQuerySet([]),
            ),
            patch.object(
                AutoScalingGroupManager,
                "list",
                return_value=[autoscaling_group],
            ),
        ):
            in_use = manager.in_use(tags={"Environment": "test"})

        assert [ami.ImageId for ami in in_use] == [used_ami.ImageId]
