from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import (
    CreateFlowLogsResult,
    DeleteFlowLogsResult,
    FlowLog,
    FlowLogManager,
)


class TestFlowLogManagerLifecycle:
    @patch("boto3.client")
    def test_create_wires_resource_ids_and_type(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_flow_logs.return_value = {
            "FlowLogIds": ["fl-123"],
            "Unsuccessful": [],
        }
        mock_boto3_client.return_value = mock_client

        manager = FlowLogManager()
        model = FlowLog(
            ResourceIds=["vpc-123"],
            ResourceType="VPC",
            TrafficType="ALL",
            LogDestinationType="cloud-watch-logs",
            LogGroupName="/vpc/flowlogs",
        )
        result = manager.create(model)

        mock_client.create_flow_logs.assert_called_once_with(
            ResourceIds=["vpc-123"],
            ResourceType="VPC",
            TrafficType="ALL",
            LogDestinationType="cloud-watch-logs",
            LogGroupName="/vpc/flowlogs",
        )
        assert isinstance(result, CreateFlowLogsResult)
        assert result.FlowLogIds == ["fl-123"]
        assert result.Unsuccessful == []

    @patch("boto3.client")
    def test_delete_wires_flow_log_id(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.delete_flow_logs.return_value = {"Unsuccessful": []}
        mock_boto3_client.return_value = mock_client

        manager = FlowLogManager()
        result = manager.delete("fl-123")

        mock_client.delete_flow_logs.assert_called_once_with(
            FlowLogIds=["fl-123"],
            DryRun=False,
        )
        assert isinstance(result, DeleteFlowLogsResult)
        assert result.Unsuccessful == []
