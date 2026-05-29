from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.common import Tag
from botocraft.services.datasync import (
    DataSyncAgent,
    DataSyncAgentManager,
    DataSyncLocationAzureBlobManager,
    DataSyncLocationS3,
    DataSyncLocationS3Manager,
    DataSyncTaskExecution,
    DataSyncTaskExecutionManager,
    DataSyncTaskManager,
)


def make_manager(manager_class: type[Any], client: MagicMock) -> Any:
    manager = cast("Any", object.__new__(manager_class))
    manager.client = client
    manager.session = None
    return manager


def agent_payload(agent_arn: str) -> dict[str, object]:
    return {
        "AgentArn": agent_arn,
        "Name": "demo-agent",
        "Status": "ONLINE",
        "EndpointType": "PUBLIC",
        "Platform": {"Version": "1.0.0"},
    }


def task_payload(task_arn: str) -> dict[str, object]:
    return {
        "TaskArn": task_arn,
        "Name": "demo-task",
        "Status": "AVAILABLE",
        "SourceLocationArn": "arn:aws:datasync:us-west-2:123456789012:location/loc-src",
        "DestinationLocationArn": "arn:aws:datasync:us-west-2:123456789012:location/loc-dst",
        "TaskMode": "BASIC",
    }


def task_execution_payload(task_execution_arn: str) -> dict[str, object]:
    return {
        "TaskExecutionArn": task_execution_arn,
        "Status": "SUCCESS",
        "TaskMode": "BASIC",
    }


def s3_location_payload(location_arn: str) -> dict[str, object]:
    return {
        "LocationArn": location_arn,
        "LocationUri": "s3://demo-bucket/prefix",
        "S3StorageClass": "STANDARD",
        "S3Config": {"BucketAccessRoleArn": "arn:aws:iam::123456789012:role/DataSync"},
        "AgentArns": [],
    }


def azure_location_payload(location_arn: str) -> dict[str, object]:
    return {
        "LocationArn": location_arn,
        "LocationUri": "https://acct.blob.core.windows.net/container",
        "AuthenticationType": "SAS",
        "BlobType": "BLOCK",
        "AccessTier": "HOT",
        "AgentArns": [],
    }


class TestDataSyncAgentManager:
    def test_create_refreshes_full_agent_and_hydrates_tags(self) -> None:
        agent_arn = "arn:aws:datasync:us-west-2:123456789012:agent/agent-01234567890abcde"
        client = MagicMock()
        client.create_agent.return_value = {"AgentArn": agent_arn}
        client.describe_agent.return_value = agent_payload(agent_arn)
        client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Environment", "Value": "test"}]
        }
        manager = make_manager(DataSyncAgentManager, client)

        created = manager.create(
            DataSyncAgent(
                ActivationKey="ABCDE-ABCDE-ABCDE-ABCDE-ABCDE",
                Name="demo-agent",
                Tags=[Tag(Key="Environment", Value="test")],
            )
        )

        assert isinstance(created, DataSyncAgent)
        assert created.AgentArn == agent_arn
        assert created.Tags is not None
        assert created.Tags[0].Value == "test"
        client.create_agent.assert_called_once()
        client.describe_agent.assert_called_once_with(AgentArn=agent_arn)

    def test_update_reconciles_tags_before_refresh(self) -> None:
        agent_arn = "arn:aws:datasync:us-west-2:123456789012:agent/agent-01234567890abcde"
        client = MagicMock()
        client.update_agent.return_value = {}
        client.describe_agent.return_value = agent_payload(agent_arn)
        client.list_tags_for_resource.side_effect = [
            {"Tags": [{"Key": "Old", "Value": "1"}]},
            {"Tags": [{"Key": "Environment", "Value": "prod"}]},
        ]
        manager = make_manager(DataSyncAgentManager, client)

        updated = manager.update(
            DataSyncAgent(
                AgentArn=agent_arn,
                Name="demo-agent",
                Tags=[Tag(Key="Environment", Value="prod")],
            )
        )

        assert isinstance(updated, DataSyncAgent)
        client.untag_resource.assert_called_once_with(
            ResourceArn=agent_arn,
            Keys=["Old"],
        )
        client.tag_resource.assert_called_once_with(
            ResourceArn=agent_arn,
            Tags=[{"Key": "Environment", "Value": "prod"}],
        )


class TestDataSyncTaskManager:
    @patch.object(DataSyncTaskExecutionManager, "get")
    def test_start_task_execution_returns_full_execution(
        self,
        mock_get: MagicMock,
    ) -> None:
        task_arn = "arn:aws:datasync:us-west-2:123456789012:task/task-0123456789abcdef0"
        execution_arn = (
            "arn:aws:datasync:us-west-2:123456789012:task/"
            "task-0123456789abcdef0/execution/exec-0123456789abcdef0"
        )
        client = MagicMock()
        client.start_task_execution.return_value = {"TaskExecutionArn": execution_arn}
        manager = make_manager(DataSyncTaskManager, client)
        execution = DataSyncTaskExecution(
            **task_execution_payload(execution_arn)
        )
        mock_get.return_value = execution

        started = manager.start_task_execution(task_arn)

        assert started is execution
        client.start_task_execution.assert_called_once_with(TaskArn=task_arn)
        mock_get.assert_called_once_with(execution_arn)


class TestDataSyncLocationManagers:
    def test_s3_list_filters_locations_and_hydrates_tags(self) -> None:
        location_arn = "arn:aws:datasync:us-west-2:123456789012:location/loc-01234567890abcde"
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"Locations": [{"LocationArn": location_arn, "LocationUri": "s3://demo/prefix"}]}
        ]
        client = MagicMock()
        client.get_paginator.return_value = paginator
        client.describe_location_s3.return_value = s3_location_payload(location_arn)
        client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Team", "Value": "platform"}]
        }
        manager = make_manager(DataSyncLocationS3Manager, client)

        locations = manager.list()

        assert isinstance(locations, PrimaryBoto3ModelQuerySet)
        assert len(locations) == 1
        assert isinstance(locations[0], DataSyncLocationS3)
        assert locations[0].Tags is not None
        assert locations[0].Tags[0].Key == "Team"
        paginator.paginate.assert_called_once_with(
            Filters=[
                {
                    "Name": "LocationType",
                    "Operator": "In",
                    "Values": ["S3", "OUTPOST_S3"],
                }
            ]
        )

    def test_azure_blob_list_scans_all_locations_and_skips_mismatches(self) -> None:
        bad_arn = "arn:aws:datasync:us-west-2:123456789012:location/loc-bad01234567890ab"
        good_arn = "arn:aws:datasync:us-west-2:123456789012:location/loc-good1234567890ab"
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {
                "Locations": [
                    {"LocationArn": bad_arn, "LocationUri": "s3://demo/prefix"},
                    {
                        "LocationArn": good_arn,
                        "LocationUri": "https://acct.blob.core.windows.net/container",
                    },
                ]
            }
        ]
        client = MagicMock()
        client.get_paginator.return_value = paginator
        client.describe_location_azure_blob.side_effect = [
            ClientError(
                {"Error": {"Code": "InvalidRequestException", "Message": "wrong type"}},
                "DescribeLocationAzureBlob",
            ),
            azure_location_payload(good_arn),
        ]
        client.list_tags_for_resource.return_value = {"Tags": []}
        manager = make_manager(DataSyncLocationAzureBlobManager, client)

        locations = manager.list()

        assert isinstance(locations, PrimaryBoto3ModelQuerySet)
        assert len(locations) == 1
        assert locations[0].LocationArn == good_arn
        paginator.paginate.assert_called_once_with()
