from __future__ import annotations

from unittest.mock import MagicMock, patch

from botocraft.services.ec2 import EC2VpcEndpointManager


class TestEC2VpcEndpointManagerModify:
    @patch("boto3.client")
    def test_modify_wires_endpoint_and_private_dns(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.modify_vpc_endpoint.return_value = {"Return": True}
        mock_boto3_client.return_value = mock_client

        manager = EC2VpcEndpointManager()
        updated = manager.modify("vpce-123", PrivateDnsEnabled=False)

        mock_client.modify_vpc_endpoint.assert_called_once_with(
            VpcEndpointId="vpce-123",
            PrivateDnsEnabled=False,
            DryRun=False,
        )
        assert updated is True

    @patch("boto3.client")
    def test_modify_returns_none_when_response_omits_return(
        self, mock_boto3_client: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_client.modify_vpc_endpoint.return_value = {}
        mock_boto3_client.return_value = mock_client

        manager = EC2VpcEndpointManager()
        updated = manager.modify("vpce-123", PolicyDocument='{"Statement":[]}')

        mock_client.modify_vpc_endpoint.assert_called_once_with(
            VpcEndpointId="vpce-123",
            PolicyDocument='{"Statement":[]}',
            DryRun=False,
        )
        assert updated is None
