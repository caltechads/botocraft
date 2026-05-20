from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import (
    CreateFlowLogsResult,
    DeleteFlowLogsResult,
    EC2VpcEndpointManager,
    FlowLog,
    FlowLogManager,
)


class TestFlowLogManagerUnsuccessful:
    @patch("boto3.client")
    def test_create_surfaces_unsuccessful_entries(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_flow_logs.return_value = {
            "FlowLogIds": [],
            "Unsuccessful": [
                {
                    "ResourceId": "vpc-bad",
                    "Error": {
                        "Code": "InvalidParameter",
                        "Message": "Resource not found",
                    },
                },
            ],
        }
        mock_boto3_client.return_value = mock_client

        manager = FlowLogManager()
        result = manager.create(
            FlowLog(
                ResourceIds=["vpc-bad"],
                ResourceType="VPC",
                TrafficType="ALL",
            )
        )

        assert isinstance(result, CreateFlowLogsResult)
        assert result.FlowLogIds == []
        assert result.Unsuccessful is not None
        assert len(result.Unsuccessful) == 1
        assert result.Unsuccessful[0].ResourceId == "vpc-bad"

    @patch("boto3.client")
    def test_delete_surfaces_unsuccessful_entries(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.delete_flow_logs.return_value = {
            "Unsuccessful": [
                {
                    "ResourceId": "fl-bad",
                    "Error": {
                        "Code": "InvalidFlowLogId.NotFound",
                        "Message": "Flow Log was not found",
                    },
                },
            ],
        }
        mock_boto3_client.return_value = mock_client

        manager = FlowLogManager()
        result = manager.delete("fl-bad")

        assert isinstance(result, DeleteFlowLogsResult)
        assert result.Unsuccessful is not None
        assert len(result.Unsuccessful) == 1


class TestEC2VpcEndpointManagerModifyKwargs:
    @patch("boto3.client")
    def test_modify_wires_subnet_and_security_group_changes(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.modify_vpc_endpoint.return_value = {"Return": True}
        mock_boto3_client.return_value = mock_client

        manager = EC2VpcEndpointManager()
        updated = manager.modify(
            "vpce-123",
            AddSubnetIds=["subnet-a"],
            RemoveSubnetIds=["subnet-b"],
            AddSecurityGroupIds=["sg-a"],
            RemoveSecurityGroupIds=["sg-b"],
        )

        mock_client.modify_vpc_endpoint.assert_called_once_with(
            VpcEndpointId="vpce-123",
            AddSubnetIds=["subnet-a"],
            RemoveSubnetIds=["subnet-b"],
            AddSecurityGroupIds=["sg-a"],
            RemoveSecurityGroupIds=["sg-b"],
            DryRun=False,
        )
        assert updated is True
