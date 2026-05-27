from collections import OrderedDict
from unittest.mock import MagicMock, patch

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
from botocraft.services.codeconnections import (
    Connection,
    ConnectionManager,
    Host,
    HostManager,
    RepositorySyncDefinition,
    RepositorySyncDefinitionManager,
    SyncBlocker,
    SyncBlockerManager,
    SyncBlockerSummary,
    SyncBlockerSummaryManager,
    SyncConfiguration,
    SyncConfigurationManager,
)


def _connection_payload(name: str) -> dict[str, object]:
    return {
        "ConnectionName": name,
        "ConnectionArn": (
            f"arn:aws:codeconnections:us-west-2:123456789012:connection/{name}"
        ),
        "ProviderType": "GitHub",
        "OwnerAccountId": "123456789012",
        "ConnectionStatus": "AVAILABLE",
    }


def _host_payload(name: str) -> dict[str, object]:
    return {
        "Name": name,
        "HostArn": f"arn:aws:codeconnections:us-west-2:123456789012:host/{name}",
        "ProviderType": "GitHubEnterpriseServer",
        "ProviderEndpoint": "https://git.example.com",
        "VpcConfiguration": {
            "VpcId": "vpc-12345678",
            "SubnetIds": ["subnet-12345678"],
            "SecurityGroupIds": ["sg-12345678"],
        },
        "Status": "AVAILABLE",
    }


def _sync_configuration_payload(resource_name: str) -> dict[str, object]:
    return {
        "Branch": "main",
        "ConfigFile": "template.yaml",
        "OwnerId": "octocat",
        "ProviderType": "GitHub",
        "RepositoryLinkId": "11111111-2222-3333-4444-555555555555",
        "RepositoryName": "demo",
        "ResourceName": resource_name,
        "RoleArn": "arn:aws:iam::123456789012:role/SyncRole",
        "SyncType": "CFN_STACK_SYNC",
        "PublishDeploymentStatus": "ENABLED",
        "TriggerResourceUpdateOn": "ANY_CHANGE",
        "PullRequestComment": "DISABLED",
    }


class TestConnectionManager:
    @patch("boto3.client")
    def test_create_connection_hydrates_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.create_connection.return_value = {
            "ConnectionArn": (
                "arn:aws:codeconnections:us-west-2:123456789012:connection/demo"
            ),
            "Tags": [{"Key": "Environment", "Value": "test"}],
        }
        mock_client.get_connection.return_value = {
            "Connection": _connection_payload("demo"),
        }
        mock_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Environment", "Value": "test"}],
        }
        mock_boto3_client.return_value = mock_client

        manager = ConnectionManager()
        model = Connection(ConnectionName="demo", ProviderType="GitHub")
        connection = manager.create(model)

        assert isinstance(connection, Connection)
        assert connection.ConnectionName == "demo"
        assert connection.ConnectionStatus == "AVAILABLE"
        assert connection.Tags is not None
        assert connection.Tags[0].Key == "Environment"

    @patch("boto3.client")
    def test_list_connections_enriches_tags(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_connections.return_value = {
            "Connections": [_connection_payload("demo")]
        }
        mock_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Environment", "Value": "test"}],
        }
        mock_boto3_client.return_value = mock_client

        manager = ConnectionManager()
        connections = manager.list()

        assert isinstance(connections, PrimaryBoto3ModelQuerySet)
        assert len(connections) == 1
        assert isinstance(connections[0], Connection)
        assert connections[0].Tags is not None
        assert connections[0].Tags[0].Value == "test"


class TestHostManager:
    @patch("boto3.client")
    def test_create_host_hydrates_model(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_host.return_value = {
            "HostArn": "arn:aws:codeconnections:us-west-2:123456789012:host/demo",
            "Tags": [{"Key": "Environment", "Value": "test"}],
        }
        mock_client.get_host.return_value = {
            key: value
            for key, value in _host_payload("demo").items()
            if key != "HostArn"
        }
        mock_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Environment", "Value": "test"}],
        }
        mock_boto3_client.return_value = mock_client

        manager = HostManager()
        model = Host(
            Name="demo",
            ProviderType="GitHubEnterpriseServer",
            ProviderEndpoint="https://git.example.com",
            VpcConfiguration={
                "VpcId": "vpc-12345678",
                "SubnetIds": ["subnet-12345678"],
                "SecurityGroupIds": ["sg-12345678"],
            },
        )
        host = manager.create(model)

        assert isinstance(host, Host)
        assert host.HostArn is not None
        assert host.HostArn.endswith("host/demo")
        assert host.Tags is not None
        assert host.Tags[0].Value == "test"

    @patch("boto3.client")
    def test_update_host_refetches_model(self, mock_boto3_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.update_host.return_value = {}
        mock_client.get_host.return_value = {
            key: value
            for key, value in _host_payload("demo").items()
            if key != "HostArn"
        }
        mock_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Environment", "Value": "test"}],
        }
        mock_boto3_client.return_value = mock_client

        manager = HostManager()
        host = Host(
            Name="demo",
            HostArn="arn:aws:codeconnections:us-west-2:123456789012:host/demo",
            ProviderType="GitHubEnterpriseServer",
            ProviderEndpoint="https://git.example.com",
            VpcConfiguration={
                "VpcId": "vpc-12345678",
                "SubnetIds": ["subnet-12345678"],
                "SecurityGroupIds": ["sg-12345678"],
            },
        )

        updated = manager.update(host)

        assert isinstance(updated, Host)
        assert updated.HostArn is not None
        assert updated.HostArn.endswith("host/demo")
        assert updated.Tags is not None
        assert updated.Tags[0].Key == "Environment"


class TestSyncConfigurationManager:
    @patch("boto3.client")
    def test_sync_configuration_crud_mappings(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        payload = _sync_configuration_payload("demo-stack")
        mock_client.create_sync_configuration.return_value = {
            "SyncConfiguration": payload,
        }
        mock_client.get_sync_configuration.return_value = {
            "SyncConfiguration": payload,
        }
        mock_client.update_sync_configuration.return_value = {
            "SyncConfiguration": payload,
        }
        mock_client.list_sync_configurations.return_value = {
            "SyncConfigurations": [payload]
        }
        mock_client.delete_sync_configuration.return_value = {}
        mock_boto3_client.return_value = mock_client

        manager = SyncConfigurationManager()
        created = manager.create(
            SyncConfiguration(
                Branch="main",
                ConfigFile="template.yaml",
                OwnerId="octocat",
                ProviderType="GitHub",
                RepositoryLinkId="11111111-2222-3333-4444-555555555555",
                RepositoryName="demo",
                ResourceName="demo-stack",
                RoleArn="arn:aws:iam::123456789012:role/SyncRole",
                SyncType="CFN_STACK_SYNC",
            )
        )
        fetched = manager.get(
            SyncType="CFN_STACK_SYNC",
            ResourceName="demo-stack",
        )
        listed = manager.list(
            RepositoryLinkId="11111111-2222-3333-4444-555555555555",
            SyncType="CFN_STACK_SYNC",
        )
        updated = manager.update(
            SyncConfiguration(
                Branch="main",
                ConfigFile="template.yaml",
                OwnerId="octocat",
                ProviderType="GitHub",
                RepositoryLinkId="11111111-2222-3333-4444-555555555555",
                RepositoryName="demo",
                ResourceName="demo-stack",
                RoleArn="arn:aws:iam::123456789012:role/SyncRole",
                SyncType="CFN_STACK_SYNC",
            )
        )
        manager.delete(
            SyncType="CFN_STACK_SYNC",
            ResourceName="demo-stack",
        )

        assert isinstance(created, SyncConfiguration)
        assert isinstance(fetched, SyncConfiguration)
        assert isinstance(listed, PrimaryBoto3ModelQuerySet)
        assert isinstance(listed[0], SyncConfiguration)
        assert isinstance(updated, SyncConfiguration)
        assert created.pk == OrderedDict(
            {
                "RepositoryLinkId": "11111111-2222-3333-4444-555555555555",
                "SyncType": "CFN_STACK_SYNC",
                "ResourceName": "demo-stack",
            }
        )


class TestRepositorySyncDefinitionManager:
    @patch("boto3.client")
    def test_list_repository_sync_definitions_adds_scope(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.list_repository_sync_definitions.return_value = {
            "RepositorySyncDefinitions": [
                {
                    "Branch": "main",
                    "Directory": "/",
                    "Parent": "stack",
                    "Target": "demo",
                }
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = RepositorySyncDefinitionManager()
        definitions = manager.list(
            RepositoryLinkId="11111111-2222-3333-4444-555555555555",
            SyncType="CFN_STACK_SYNC",
        )

        assert isinstance(definitions, PrimaryBoto3ModelQuerySet)
        assert len(definitions) == 1
        assert isinstance(definitions[0], RepositorySyncDefinition)
        assert definitions[0].RepositoryLinkId == (
            "11111111-2222-3333-4444-555555555555"
        )
        assert definitions[0].SyncType == "CFN_STACK_SYNC"


class TestSyncBlockerSummaryManager:
    @patch("boto3.client")
    def test_get_sync_blocker_summary_adds_context(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.get_sync_blocker_summary.return_value = {
            "SyncBlockerSummary": {
                "ResourceName": "demo-stack",
                "ParentResourceName": "demo-parent",
                "LatestBlockers": [
                    {
                        "Id": "blocker-1",
                        "Type": "AUTOMATED",
                        "Status": "ACTIVE",
                        "CreatedReason": "Needs review",
                        "CreatedAt": "2024-03-29T00:00:00+00:00",
                    }
                ],
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = SyncBlockerSummaryManager()
        summary = manager.get(
            SyncType="CFN_STACK_SYNC",
            ResourceName="demo-stack",
        )

        assert isinstance(summary, SyncBlockerSummary)
        assert summary.SyncType == "CFN_STACK_SYNC"
        assert summary.LatestBlockers is not None
        assert summary.LatestBlockers[0].ResourceName == "demo-stack"
        assert summary.LatestBlockers[0].ParentResourceName == "demo-parent"


class TestSyncBlockerManager:
    @patch("boto3.client")
    def test_update_sync_blocker_returns_public_model(
        self,
        mock_boto3_client: MagicMock,
    ) -> None:
        mock_client = MagicMock()
        mock_client.update_sync_blocker.return_value = {
            "ResourceName": "demo-stack",
            "ParentResourceName": "demo-parent",
            "SyncBlocker": {
                "Id": "blocker-1",
                "Type": "AUTOMATED",
                "Status": "RESOLVED",
                "CreatedReason": "Needs review",
                "CreatedAt": "2024-03-29T00:00:00+00:00",
                "ResolvedReason": "Done",
                "ResolvedAt": "2024-03-30T00:00:00+00:00",
            },
        }
        mock_boto3_client.return_value = mock_client

        manager = SyncBlockerManager()
        blocker = manager.update(
            Id="blocker-1",
            SyncType="CFN_STACK_SYNC",
            ResourceName="demo-stack",
            ResolvedReason="Done",
        )

        assert isinstance(blocker, SyncBlocker)
        assert blocker.SyncType == "CFN_STACK_SYNC"
        assert blocker.ResourceName == "demo-stack"
        assert blocker.ParentResourceName == "demo-parent"
