from unittest.mock import MagicMock, patch

from botocraft.services.ecs import (
    CapacityProvider,
    CapacityProviderManager,
    Cluster,
    ClusterManager,
    ContainerInstance,
    Daemon,
    DaemonDeployment,
    DaemonDeploymentManager,
    DaemonManager,
    DaemonRevision,
    DaemonRevisionManager,
    DaemonTaskDefinition,
    DaemonTaskDefinitionManager,
    ExpressGatewayService,
    ExpressGatewayServiceManager,
    PrimaryBoto3ModelQuerySet,
    Service,
    ServiceDeployment,
    ServiceRevision,
    ServiceRevisionManager,
    Task,
    TaskDefinition,
    TaskSet,
    TaskSetManager,
)


def _manager_proxy(method_name: str, return_value):
    manager = MagicMock()
    setattr(manager, method_name, MagicMock(return_value=return_value))
    objects = MagicMock()
    objects.using.return_value = manager
    return objects, manager


class TestClusterManager:
    @patch("boto3.client")
    def test_get_many(self, mock_boto3_client):
        # Setup mock response data
        mock_response = {
            "ResponseMetadata": {
                "HTTPHeaders": {
                    "content-length": "16819",
                    "content-type": "application/x-amz-json-1.1",
                    "date": "Wed, 28 May 2025 18:39:17 GMT",
                    "x-amzn-requestid": "699f0880-ec6d-41a7-adbd-1b0adac428f0",
                },
                "HTTPStatusCode": 200,
                "RequestId": "699f0880-ec6d-41a7-adbd-1b0adac428f0",
                "RetryAttempts": 0,
            },
            "clusters": [
                {
                    "activeServicesCount": 7,
                    "capacityProviders": [],
                    "clusterArn": "arn:aws:ecs:us-west-2:467892444047:cluster/dropbox-prod",
                    "clusterName": "dropbox-prod",
                    "defaultCapacityProviderStrategy": [],
                    "pendingTasksCount": 0,
                    "registeredContainerInstancesCount": 8,
                    "runningTasksCount": 6,
                    "settings": [],
                    "statistics": [],
                    "status": "ACTIVE",
                    "tags": [
                        {"key": "Group", "value": "IMSS ADS"},
                        {"key": "Project", "value": "dropbox"},
                        {"key": "Environment", "value": "prod"},
                        {"key": "Client", "value": "IMSS"},
                        {"key": "deployfish:autoscalingGroup", "value": "dropbox-prod"},
                        {"key": "Contact", "value": "imss-ads-staff@caltech.edu"},
                    ],
                },
                {
                    "activeServicesCount": 1,
                    "capacityProviders": [],
                    "clusterArn": "arn:aws:ecs:us-west-2:467892444047:cluster/dropbox-test",
                    "clusterName": "dropbox-test",
                    "defaultCapacityProviderStrategy": [],
                    "pendingTasksCount": 0,
                    "registeredContainerInstancesCount": 1,
                    "runningTasksCount": 1,
                    "settings": [],
                    "statistics": [],
                    "status": "ACTIVE",
                    "tags": [
                        {"key": "Group", "value": "IMSS ADS"},
                        {"key": "Project", "value": "dropbox"},
                        {"key": "Environment", "value": "test"},
                        {"key": "Client", "value": "IMSS"},
                        {"key": "deployfish:autoscalingGroup", "value": "dropbox-test"},
                        {"key": "Contact", "value": "imss-ads-staff@caltech.edu"},
                    ],
                },
            ],
            "failures": [],
        }

        # Configure the mock client
        mock_client = MagicMock()
        mock_client.describe_clusters.return_value = mock_response
        mock_boto3_client.return_value = mock_client

        # Create manager instance and call get_many
        manager = ClusterManager()

        # Test with specific cluster names
        clusters = manager.get_many(clusters=["dropbox-prod", "dropbox-test"])

        # Verify mock was called with correct parameters
        mock_client.describe_clusters.assert_called_once_with(
            clusters=["dropbox-prod", "dropbox-test"],
            include=["ATTACHMENTS", "CONFIGURATIONS", "SETTINGS", "STATISTICS", "TAGS"],
        )

        # Verify results
        assert isinstance(clusters, PrimaryBoto3ModelQuerySet)
        assert len(clusters) == 2

        # Check the first cluster details
        cluster1 = clusters[0]
        assert isinstance(cluster1, Cluster)
        assert cluster1.clusterName == "dropbox-prod"
        assert (
            cluster1.clusterArn
            == "arn:aws:ecs:us-west-2:467892444047:cluster/dropbox-prod"
        )
        assert cluster1.status == "ACTIVE"
        assert cluster1.activeServicesCount == 7
        assert cluster1.runningTasksCount == 6

        # Verify tags were properly assigned
        assert len(cluster1.Tags) == 6
        assert cluster1.Tags[0].key == "Group"
        assert cluster1.Tags[0].value == "IMSS ADS"

        # Check the second cluster details
        cluster2 = clusters[1]
        assert cluster2.clusterName == "dropbox-test"
        assert cluster2.runningTasksCount == 1

    @patch("boto3.client")
    def test_get_many_with_full_response(self, mock_boto3_client):
        """Test with the full response data containing all clusters"""
        # The full mock response would be too large to include here,
        # but we can simulate it with a smaller sample

        # Setup mock response with 28 clusters (as in the provided data)
        mock_response = {
            "ResponseMetadata": {
                "HTTPHeaders": {},
                "HTTPStatusCode": 200,
                "RequestId": "",
                "RetryAttempts": 0,
            },
            "clusters": [
                # Create sample data for 28 clusters
                {
                    "clusterArn": f"arn:aws:ecs:us-west-2:467892444047:cluster/cluster-{i}",
                    "clusterName": f"cluster-{i}",
                    "status": "ACTIVE",
                    "tags": [{"key": "Test", "value": "Value"}],
                }
                for i in range(28)
            ],
            "failures": [],
        }

        # Configure the mock client
        mock_client = MagicMock()
        mock_client.describe_clusters.return_value = mock_response
        mock_boto3_client.return_value = mock_client

        # Create manager instance and call get_many without specific clusters
        manager = ClusterManager()
        clusters = manager.get_many()

        # Verify results
        assert isinstance(clusters, PrimaryBoto3ModelQuerySet)
        assert len(clusters) == 28

        # Test that each cluster is properly created
        for i, cluster in enumerate(clusters):
            assert isinstance(cluster, Cluster)
            assert cluster.clusterName == f"cluster-{i}"
            assert (
                cluster.clusterArn
                == f"arn:aws:ecs:us-west-2:467892444047:cluster/cluster-{i}"
            )

    @patch("boto3.client")
    def test_get_many_empty_result(self, mock_boto3_client):
        """Test behavior when no clusters are returned"""
        mock_response = {
            "ResponseMetadata": {
                "HTTPHeaders": {},
                "HTTPStatusCode": 200,
                "RequestId": "",
                "RetryAttempts": 0,
            },
            "clusters": [],
            "failures": [],
        }

        # Configure the mock client
        mock_client = MagicMock()
        mock_client.describe_clusters.return_value = mock_response
        mock_boto3_client.return_value = mock_client

        # Create manager instance and call get_many
        manager = ClusterManager()
        clusters = manager.get_many(clusters=["non-existent-cluster"])

        # Verify empty queryset is returned
        assert isinstance(clusters, PrimaryBoto3ModelQuerySet)
        assert len(clusters) == 0
        assert bool(clusters) is False


class TestCapacityProviderManager:
    @patch("boto3.client")
    def test_list_unfiltered_paginates(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.describe_capacity_providers.side_effect = [
            {
                "capacityProviders": [
                    {
                        "capacityProviderArn": "cp-arn-1",
                        "name": "cp-1",
                        "status": "ACTIVE",
                        "tags": [{"key": "Environment", "value": "prod"}],
                    }
                ],
                "nextToken": "token-1",
            },
            {
                "capacityProviders": [
                    {
                        "capacityProviderArn": "cp-arn-2",
                        "name": "cp-2",
                        "status": "ACTIVE",
                        "tags": [{"key": "Environment", "value": "test"}],
                    }
                ]
            },
        ]
        mock_boto3_client.return_value = mock_client

        manager = CapacityProviderManager()
        providers = manager.list(
            cluster="cluster-arn",
            include=["TAGS"],
        )

        assert isinstance(providers, PrimaryBoto3ModelQuerySet)
        assert [provider.name for provider in providers] == ["cp-1", "cp-2"]
        assert providers[0].Tags[0].key == "Environment"
        assert mock_client.describe_capacity_providers.call_count == 2
        first_call = mock_client.describe_capacity_providers.call_args_list[0]
        second_call = mock_client.describe_capacity_providers.call_args_list[1]
        assert first_call.kwargs == {
            "cluster": "cluster-arn",
            "include": ["TAGS"],
            "maxResults": 100,
        }
        assert second_call.kwargs == {
            "cluster": "cluster-arn",
            "include": ["TAGS"],
            "maxResults": 100,
            "nextToken": "token-1",
        }

    @patch("boto3.client")
    def test_list_filtered_delegates_to_get_many(self, mock_boto3_client):
        mock_boto3_client.return_value = MagicMock()
        manager = CapacityProviderManager()
        expected = PrimaryBoto3ModelQuerySet(
            [CapacityProvider(capacityProviderArn="cp-arn-1", name="cp-1")]
        )
        manager.get_many = MagicMock(return_value=expected)

        result = manager.list(
            capacityProviders=["cp-1"],
            cluster="cluster-arn",
            include=["TAGS"],
        )

        assert result is expected
        manager.get_many.assert_called_once_with(
            capacityProviders=["cp-1"],
            cluster="cluster-arn",
            include=["TAGS"],
        )


class TestTaskSetManager:
    @patch("boto3.client")
    def test_list_scoped_describe(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.describe_task_sets.return_value = {
            "taskSets": [
                {
                    "taskSetArn": "ts-arn-1",
                    "serviceArn": "service-arn",
                    "clusterArn": "cluster-arn",
                    "taskDefinition": "family:1",
                    "status": "ACTIVE",
                    "tags": [{"key": "Team", "value": "infra"}],
                }
            ]
        }
        mock_boto3_client.return_value = mock_client

        manager = TaskSetManager()
        task_sets = manager.list(
            service="service-arn",
            cluster="cluster-arn",
            include=["TAGS"],
        )

        assert isinstance(task_sets, PrimaryBoto3ModelQuerySet)
        assert len(task_sets) == 1
        assert task_sets[0].taskSetArn == "ts-arn-1"
        assert task_sets[0].Tags[0].key == "Team"
        mock_client.describe_task_sets.assert_called_once_with(
            service="service-arn",
            cluster="cluster-arn",
            include=["TAGS"],
        )


class TestDaemonManager:
    @patch("boto3.client")
    def test_list_paginates_and_hydrates(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.list_daemons.side_effect = [
            {
                "daemonSummariesList": [
                    {
                        "daemonArn": "daemon-arn-1",
                        "clusterArn": "cluster-arn",
                    }
                ],
                "nextToken": "token-1",
            },
            {
                "daemonSummariesList": [
                    {
                        "daemonArn": "daemon-arn-2",
                        "clusterArn": "cluster-arn",
                    }
                ]
            },
        ]
        mock_boto3_client.return_value = mock_client

        manager = DaemonManager()
        manager.get = MagicMock(
            side_effect=[
                Daemon(daemonArn="daemon-arn-1", clusterArn="cluster-arn"),
                Daemon(daemonArn="daemon-arn-2", clusterArn="cluster-arn"),
            ]
        )

        daemons = manager.list(clusterArn="cluster-arn")

        assert isinstance(daemons, PrimaryBoto3ModelQuerySet)
        assert [daemon.daemonArn for daemon in daemons] == ["daemon-arn-1", "daemon-arn-2"]
        assert mock_client.list_daemons.call_args_list[0].kwargs == {
            "clusterArn": "cluster-arn",
            "maxResults": 100,
        }
        assert mock_client.list_daemons.call_args_list[1].kwargs == {
            "clusterArn": "cluster-arn",
            "maxResults": 100,
            "nextToken": "token-1",
        }
        manager.get.assert_any_call(daemonArn="daemon-arn-1")
        manager.get.assert_any_call(daemonArn="daemon-arn-2")

    @patch("boto3.client")
    def test_create_update_delete_use_follow_up_contract(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.create_daemon.return_value = {
            "daemonArn": "daemon-arn-1",
        }
        mock_client.update_daemon.return_value = {
            "daemonArn": "daemon-arn-1",
        }
        mock_client.delete_daemon.return_value = {
            "daemonArn": "daemon-arn-1",
        }
        mock_boto3_client.return_value = mock_client

        manager = DaemonManager()
        created = Daemon(
            daemonArn="daemon-arn-1",
            daemonName="daemon-1",
            clusterArn="cluster-arn",
            daemonTaskDefinitionArn="task-def-arn-1",
            capacityProviderArns=["cp-arn-1"],
        )
        manager.get = MagicMock(return_value=created)

        daemon = Daemon(
            daemonName="daemon-1",
            clusterArn="cluster-arn",
            daemonTaskDefinitionArn="task-def-arn-1",
            capacityProviderArns=["cp-arn-1"],
        )
        assert manager.create(daemon) is created
        mock_client.create_daemon.assert_called_once_with(
            daemonName="daemon-1",
            clusterArn="cluster-arn",
            daemonTaskDefinitionArn="task-def-arn-1",
            capacityProviderArns=["cp-arn-1"],
        )
        manager.get.assert_called_with(daemonArn="daemon-arn-1")

        manager.get.reset_mock(return_value=True, side_effect=True)
        manager.get.return_value = created
        daemon.daemonArn = "daemon-arn-1"
        assert manager.update(daemon) is created
        mock_client.update_daemon.assert_called_once_with(
            daemonArn="daemon-arn-1",
            daemonTaskDefinitionArn="task-def-arn-1",
            capacityProviderArns=["cp-arn-1"],
        )
        manager.get.assert_called_with(daemonArn="daemon-arn-1")

        manager.get.reset_mock(return_value=True, side_effect=True)
        manager.get.return_value = created
        assert manager.delete(created) is created
        manager.get.assert_called_with(daemonArn="daemon-arn-1")
        mock_client.delete_daemon.assert_called_once_with(daemonArn="daemon-arn-1")


class TestDaemonTaskDefinitionManager:
    @patch("boto3.client")
    def test_list_hydrates_from_summaries(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.list_daemon_task_definitions.side_effect = [
            {
                "daemonTaskDefinitions": [
                    {
                        "daemonTaskDefinitionArn": "daemon-task-def-arn-1",
                    }
                ],
                "nextToken": "token-1",
            },
            {
                "daemonTaskDefinitions": [
                    {
                        "daemonTaskDefinitionArn": "daemon-task-def-arn-2",
                    }
                ]
            },
        ]
        mock_boto3_client.return_value = mock_client

        manager = DaemonTaskDefinitionManager()
        manager.get = MagicMock(
            side_effect=[
                DaemonTaskDefinition(daemonTaskDefinitionArn="daemon-task-def-arn-1"),
                DaemonTaskDefinition(daemonTaskDefinitionArn="daemon-task-def-arn-2"),
            ]
        )

        task_definitions = manager.list(familyPrefix="agent")

        assert isinstance(task_definitions, PrimaryBoto3ModelQuerySet)
        assert [td.daemonTaskDefinitionArn for td in task_definitions] == [
            "daemon-task-def-arn-1",
            "daemon-task-def-arn-2",
        ]
        assert mock_client.list_daemon_task_definitions.call_args_list[0].kwargs == {
            "familyPrefix": "agent",
            "maxResults": 100,
        }
        assert mock_client.list_daemon_task_definitions.call_args_list[1].kwargs == {
            "familyPrefix": "agent",
            "maxResults": 100,
            "nextToken": "token-1",
        }
        manager.get.assert_any_call(
            daemonTaskDefinition="daemon-task-def-arn-1"
        )
        manager.get.assert_any_call(
            daemonTaskDefinition="daemon-task-def-arn-2"
        )

    @patch("boto3.client")
    def test_create_and_delete_use_follow_up_contract(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.register_daemon_task_definition.return_value = {
            "daemonTaskDefinitionArn": "daemon-task-def-arn-1",
        }
        mock_client.delete_daemon_task_definition.return_value = {
            "daemonTaskDefinitionArn": "daemon-task-def-arn-1",
        }
        mock_boto3_client.return_value = mock_client

        manager = DaemonTaskDefinitionManager()
        created = DaemonTaskDefinition(
            daemonTaskDefinitionArn="daemon-task-def-arn-1",
            family="agent",
            containerDefinitions=[],
        )
        manager.get = MagicMock(return_value=created)

        task_definition = DaemonTaskDefinition(
            family="agent",
            containerDefinitions=[],
        )
        assert manager.create(task_definition) is created
        mock_client.register_daemon_task_definition.assert_called_once_with(
            family="agent",
            containerDefinitions=[],
        )
        manager.get.assert_called_with(
            daemonTaskDefinition="daemon-task-def-arn-1"
        )

        manager.get.reset_mock(return_value=True, side_effect=True)
        manager.get.return_value = created
        assert manager.delete(created) is created
        manager.get.assert_called_with(
            daemonTaskDefinition="daemon-task-def-arn-1"
        )
        mock_client.delete_daemon_task_definition.assert_called_once_with(
            daemonTaskDefinition="daemon-task-def-arn-1"
        )


class TestDaemonRevisionManager:
    @patch("boto3.client")
    def test_get_many(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.describe_daemon_revisions.return_value = {
            "daemonRevisions": [
                {
                    "daemonRevisionArn": "daemon-revision-arn-1",
                    "daemonArn": "daemon-arn-1",
                    "clusterArn": "cluster-arn",
                    "daemonTaskDefinitionArn": "task-def-arn-1",
                },
                {
                    "daemonRevisionArn": "daemon-revision-arn-2",
                    "daemonArn": "daemon-arn-1",
                    "clusterArn": "cluster-arn",
                    "daemonTaskDefinitionArn": "task-def-arn-2",
                },
            ],
            "failures": [],
        }
        mock_boto3_client.return_value = mock_client

        manager = DaemonRevisionManager()
        revisions = manager.get_many(
            daemonRevisionArns=["daemon-revision-arn-1", "daemon-revision-arn-2"]
        )

        assert isinstance(revisions, PrimaryBoto3ModelQuerySet)
        assert [revision.daemonRevisionArn for revision in revisions] == [
            "daemon-revision-arn-1",
            "daemon-revision-arn-2",
        ]
        mock_client.describe_daemon_revisions.assert_called_once_with(
            daemonRevisionArns=["daemon-revision-arn-1", "daemon-revision-arn-2"]
        )


class TestDaemonDeploymentManager:
    @patch("boto3.client")
    def test_list(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.list_daemon_deployments.return_value = {
            "daemonDeployments": [
                {
                    "daemonDeploymentArn": "deployment-arn-1",
                    "daemonArn": "daemon-arn-1",
                    "clusterArn": "cluster-arn",
                    "targetDaemonRevisionArn": "daemon-revision-arn-1",
                }
            ],
            "nextToken": "token-1",
        }
        mock_boto3_client.return_value = mock_client

        manager = DaemonDeploymentManager()
        deployments = manager.list(
            daemonArn="daemon-arn-1",
            status=["IN_PROGRESS"],
            createdAt={"before": "2026-05-18T00:00:00Z"},
            maxResults=5,
            nextToken="token-0",
        )

        assert isinstance(deployments, PrimaryBoto3ModelQuerySet)
        assert deployments[0].daemonDeploymentArn == "deployment-arn-1"
        mock_client.list_daemon_deployments.assert_called_once_with(
            daemonArn="daemon-arn-1",
            status=["IN_PROGRESS"],
            createdAt={"before": "2026-05-18T00:00:00Z"},
            maxResults=5,
            nextToken="token-0",
        )


class TestExpressGatewayServiceManager:
    @patch("boto3.client")
    def test_list_hydrates_namespace_scope(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.list_services_by_namespace.return_value = {
            "serviceArns": ["service-arn-1", "service-arn-2"],
            "nextToken": "token-1",
        }
        mock_boto3_client.return_value = mock_client

        manager = ExpressGatewayServiceManager()
        manager.get = MagicMock(
            side_effect=[
                ExpressGatewayService(serviceArn="service-arn-1", serviceName="svc-1"),
                ExpressGatewayService(serviceArn="service-arn-2", serviceName="svc-2"),
            ]
        )

        services = manager.list(namespace="team-a", maxResults=10, nextToken="token-0")

        assert isinstance(services, PrimaryBoto3ModelQuerySet)
        assert [service.serviceArn for service in services] == [
            "service-arn-1",
            "service-arn-2",
        ]
        mock_client.list_services_by_namespace.assert_called_once_with(
            namespace="team-a",
            maxResults=10,
            nextToken="token-0",
        )
        manager.get.assert_any_call(serviceArn="service-arn-1")
        manager.get.assert_any_call(serviceArn="service-arn-2")

    @patch("boto3.client")
    def test_update_uses_follow_up_get(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.update_express_gateway_service.return_value = {
            "service": {
                "serviceArn": "service-arn-1",
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = ExpressGatewayServiceManager()
        expected = ExpressGatewayService(
            serviceArn="service-arn-1",
            serviceName="svc-1",
            cluster="cluster-arn",
            cpu="1024",
        )
        manager.get = MagicMock(return_value=expected)

        model = ExpressGatewayService(
            serviceArn="service-arn-1",
            serviceName="svc-1",
            cluster="cluster-arn",
            cpu="1024",
        )
        assert manager.update(model) is expected
        mock_client.update_express_gateway_service.assert_called_once_with(
            serviceArn="service-arn-1",
            cpu="1024",
        )
        manager.get.assert_called_once_with(serviceArn="service-arn-1")

    @patch("boto3.client")
    def test_create_get_delete_wire_requests_and_responses(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.create_express_gateway_service.return_value = {
            "service": {
                "serviceArn": "service-arn-1",
                "serviceName": "svc-1",
                "cluster": "cluster-arn",
            }
        }
        mock_client.describe_express_gateway_service.return_value = {
            "service": {
                "serviceArn": "service-arn-1",
                "serviceName": "svc-1",
                "cluster": "cluster-arn",
            }
        }
        mock_client.delete_express_gateway_service.return_value = {
            "service": {
                "serviceArn": "service-arn-1",
                "serviceName": "svc-1",
                "cluster": "cluster-arn",
            }
        }
        mock_boto3_client.return_value = mock_client

        manager = ExpressGatewayServiceManager()
        model = ExpressGatewayService(
            serviceName="svc-1",
            cluster="cluster-arn",
            infrastructureRoleArn="arn:aws:iam::123456789012:role/infra",
        )
        created = manager.create(
            model,
            executionRoleArn="arn:aws:iam::123456789012:role/exec",
            primaryContainer={
                "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/app:1"
            },
        )
        loaded = manager.get(serviceArn="service-arn-1")
        deleted = manager.delete(serviceArn="service-arn-1")

        mock_client.create_express_gateway_service.assert_called_once_with(
            executionRoleArn="arn:aws:iam::123456789012:role/exec",
            infrastructureRoleArn="arn:aws:iam::123456789012:role/infra",
            serviceName="svc-1",
            cluster="cluster-arn",
            primaryContainer={
                "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/app:1"
            },
            tags=[],
        )
        mock_client.describe_express_gateway_service.assert_called_once_with(
            serviceArn="service-arn-1"
        )
        mock_client.delete_express_gateway_service.assert_called_once_with(
            serviceArn="service-arn-1"
        )
        assert isinstance(created, ExpressGatewayService)
        assert isinstance(loaded, ExpressGatewayService)
        assert isinstance(deleted, ExpressGatewayService)


class TestServiceRevisionManager:
    @patch("boto3.client")
    def test_list_delegates_to_get_many(self, mock_boto3_client):
        mock_boto3_client.return_value = MagicMock()
        manager = ServiceRevisionManager()
        expected = PrimaryBoto3ModelQuerySet(
            [ServiceRevision(serviceRevisionArn="revision-arn-1")]
        )
        manager.get_many = MagicMock(return_value=expected)

        result = manager.list(serviceRevisionArns=["revision-arn-1"])

        assert result is expected
        manager.get_many.assert_called_once_with(
            serviceRevisionArns=["revision-arn-1"]
        )


class TestECSRelations:
    def test_service_current_service_deployment(self):
        session = MagicMock()
        service = Service(
            serviceName="svc",
            taskDefinition="family:1",
            clusterArn="cluster-arn",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
            currentServiceDeployment="deployment-arn",
        )
        service.set_session(session)
        deployment = ServiceDeployment(serviceDeploymentArn="deployment-arn")
        objects, manager = _manager_proxy("get", deployment)

        with patch.object(ServiceDeployment, "objects", objects):
            assert service.current_service_deployment is deployment

        manager.get.assert_called_once_with(serviceDeploymentArn="deployment-arn")

    def test_service_current_service_revisions(self):
        session = MagicMock()
        service = Service(
            serviceName="svc",
            taskDefinition="family:1",
            clusterArn="cluster-arn",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
            currentServiceRevisions=[{"arn": "revision-arn-1"}, {"arn": "revision-arn-2"}],
        )
        service.set_session(session)
        revisions = PrimaryBoto3ModelQuerySet(
            [
                ServiceRevision(serviceRevisionArn="revision-arn-1"),
                ServiceRevision(serviceRevisionArn="revision-arn-2"),
            ]
        )
        objects, manager = _manager_proxy("list", revisions)

        with patch.object(ServiceRevision, "objects", objects):
            assert service.current_service_revisions is revisions

        manager.list.assert_called_once_with(
            serviceRevisionArns=["revision-arn-1", "revision-arn-2"]
        )

    def test_service_task_sets(self):
        session = MagicMock()
        service = Service(
            serviceName="svc",
            taskDefinition="family:1",
            clusterArn="cluster-arn",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
            taskSets=[{"taskSetArn": "task-set-arn-1"}, {"taskSetArn": "task-set-arn-2"}],
        )
        service.set_session(session)
        task_sets = PrimaryBoto3ModelQuerySet(
            [
                TaskSet(taskSetArn="task-set-arn-1"),
                TaskSet(taskSetArn="task-set-arn-2"),
            ]
        )
        objects, manager = _manager_proxy("list", task_sets)

        with patch.object(TaskSet, "objects", objects):
            assert service.task_sets is task_sets

        manager.list.assert_called_once_with(
            service="svc",
            cluster="cluster-arn",
            taskSets=["task-set-arn-1", "task-set-arn-2"],
        )

    def test_cluster_capacity_providers(self):
        session = MagicMock()
        cluster = Cluster(
            clusterArn="cluster-arn",
            clusterName="cluster-name",
            capacityProviders=["cp-1", "cp-2"],
        )
        cluster.set_session(session)
        providers = PrimaryBoto3ModelQuerySet(
            [
                CapacityProvider(capacityProviderArn="cp-arn-1", name="cp-1"),
                CapacityProvider(capacityProviderArn="cp-arn-2", name="cp-2"),
            ]
        )
        objects, manager = _manager_proxy("list", providers)

        with patch.object(CapacityProvider, "objects", objects):
            assert cluster.capacity_providers is providers

        manager.list.assert_called_once_with(
            capacityProviders=["cp-1", "cp-2"],
            cluster="cluster-name",
        )

    def test_task_capacity_provider(self):
        session = MagicMock()
        task = Task(
            clusterArn="cluster-arn",
            taskDefinition="family:1",
            capacityProviderName="cp-1",
        )
        task.set_session(session)
        provider = CapacityProvider(capacityProviderArn="cp-arn-1", name="cp-1")
        objects, manager = _manager_proxy("get", provider)

        with patch.object(CapacityProvider, "objects", objects):
            assert task.capacity_provider is provider

        manager.get.assert_called_once_with(
            capacityProvider="cp-1",
            cluster="cluster-arn",
        )

    def test_container_instance_cluster(self):
        session = MagicMock()
        instance = ContainerInstance(
            containerInstanceArn=(
                "arn:aws:ecs:us-west-2:123456789012:container-instance/"
                "cluster-name/0123456789abcdef"
            )
        )
        instance.set_session(session)
        cluster = Cluster(clusterArn="cluster-arn", clusterName="cluster-name")
        objects, manager = _manager_proxy("get", cluster)

        with patch.object(Cluster, "objects", objects):
            assert instance.cluster is cluster

        manager.get.assert_called_once_with(cluster="cluster-name")

    def test_container_instance_capacity_provider(self):
        session = MagicMock()
        instance = ContainerInstance(
            containerInstanceArn=(
                "arn:aws:ecs:us-west-2:123456789012:container-instance/"
                "cluster-name/0123456789abcdef"
            ),
            capacityProviderName="cp-1",
        )
        instance.set_session(session)
        provider = CapacityProvider(capacityProviderArn="cp-arn-1", name="cp-1")
        objects, manager = _manager_proxy("get", provider)

        with patch.object(CapacityProvider, "objects", objects):
            assert instance.capacity_provider is provider

        manager.get.assert_called_once_with(
            capacityProvider="cp-1",
            cluster="cluster-name",
        )

    def test_service_deployment_relations(self):
        session = MagicMock()
        deployment = ServiceDeployment(
            serviceDeploymentArn="deployment-arn",
            serviceArn="service-arn",
            clusterArn="cluster-arn",
            targetServiceRevision={"arn": "revision-arn-1"},
            sourceServiceRevisions=[{"arn": "revision-arn-2"}, {"arn": "revision-arn-3"}],
        )
        deployment.set_session(session)

        service = Service(
            serviceName="svc",
            taskDefinition="family:1",
            clusterArn="cluster-arn",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
            serviceArn="service-arn",
        )
        cluster = Cluster(clusterArn="cluster-arn", clusterName="cluster-name")
        target_revision = ServiceRevision(
            serviceRevisionArn="revision-arn-1",
            taskDefinition="family:1",
        )
        source_revisions = PrimaryBoto3ModelQuerySet(
            [
                ServiceRevision(serviceRevisionArn="revision-arn-2"),
                ServiceRevision(serviceRevisionArn="revision-arn-3"),
            ]
        )

        service_objects, service_manager = _manager_proxy("get", service)
        cluster_objects, cluster_manager = _manager_proxy("get", cluster)
        target_objects, target_manager = _manager_proxy("get", target_revision)
        source_objects, source_manager = _manager_proxy("list", source_revisions)

        with (
            patch.object(Service, "objects", service_objects),
            patch.object(Cluster, "objects", cluster_objects),
            patch.object(ServiceRevision, "objects", target_objects),
        ):
            assert deployment.service is service
            assert deployment.cluster is cluster
            assert deployment.target_service_revision is target_revision

        with patch.object(ServiceRevision, "objects", source_objects):
            assert deployment.source_service_revisions is source_revisions

        service_manager.get.assert_called_once_with(
            service="service-arn",
            cluster="cluster-arn",
        )
        cluster_manager.get.assert_called_once_with(cluster="cluster-arn")
        target_manager.get.assert_called_once_with(
            serviceRevisionArn="revision-arn-1"
        )
        source_manager.list.assert_called_once_with(
            serviceRevisionArns=["revision-arn-2", "revision-arn-3"]
        )

    def test_task_set_relations(self):
        session = MagicMock()
        task_set = TaskSet(
            taskSetArn="task-set-arn",
            serviceArn="service-arn",
            clusterArn="cluster-arn",
            taskDefinition="family:1",
        )
        task_set.set_session(session)
        service = Service(
            serviceName="svc",
            taskDefinition="family:1",
            clusterArn="cluster-arn",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
            serviceArn="service-arn",
        )
        cluster = Cluster(clusterArn="cluster-arn", clusterName="cluster-name")
        task_definition = TaskDefinition(
            taskDefinitionArn="arn:aws:ecs:us-west-2:123456789012:task-definition/family:1",
            family="family",
            containerDefinitions=[],
        )

        service_objects, service_manager = _manager_proxy("get", service)
        cluster_objects, cluster_manager = _manager_proxy("get", cluster)
        task_definition_objects, task_definition_manager = _manager_proxy(
            "get", task_definition
        )

        with (
            patch.object(Service, "objects", service_objects),
            patch.object(Cluster, "objects", cluster_objects),
            patch.object(TaskDefinition, "objects", task_definition_objects),
        ):
            assert task_set.service is service
            assert task_set.cluster is cluster
            assert task_set.task_definition is task_definition

        service_manager.get.assert_called_once_with(
            service="service-arn",
            cluster="cluster-arn",
        )
        cluster_manager.get.assert_called_once_with(cluster="cluster-arn")
        task_definition_manager.get.assert_called_once_with(taskDefinition="family:1")

    def test_service_revision_relations(self):
        session = MagicMock()
        revision = ServiceRevision(
            serviceRevisionArn="revision-arn",
            serviceArn="service-arn",
            clusterArn="cluster-arn",
            taskDefinition="family:1",
        )
        revision.set_session(session)
        service = Service(
            serviceName="svc",
            taskDefinition="family:1",
            clusterArn="cluster-arn",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
            serviceArn="service-arn",
        )
        cluster = Cluster(clusterArn="cluster-arn", clusterName="cluster-name")
        task_definition = TaskDefinition(
            taskDefinitionArn="arn:aws:ecs:us-west-2:123456789012:task-definition/family:1",
            family="family",
            containerDefinitions=[],
        )

        service_objects, service_manager = _manager_proxy("get", service)
        cluster_objects, cluster_manager = _manager_proxy("get", cluster)
        task_definition_objects, task_definition_manager = _manager_proxy(
            "get", task_definition
        )

        with (
            patch.object(Service, "objects", service_objects),
            patch.object(Cluster, "objects", cluster_objects),
            patch.object(TaskDefinition, "objects", task_definition_objects),
        ):
            assert revision.service is service
            assert revision.cluster is cluster
            assert revision.task_definition is task_definition

        service_manager.get.assert_called_once_with(
            service="service-arn",
            cluster="cluster-arn",
        )
        cluster_manager.get.assert_called_once_with(cluster="cluster-arn")
        task_definition_manager.get.assert_called_once_with(taskDefinition="family:1")

    def test_daemon_relations(self):
        session = MagicMock()
        daemon = Daemon(
            daemonArn="daemon-arn",
            clusterArn="cluster-arn",
            currentRevisions=[{"arn": "daemon-revision-arn-1"}, {"arn": "daemon-revision-arn-2"}],
        )
        daemon.set_session(session)
        cluster = Cluster(clusterArn="cluster-arn", clusterName="cluster-name")
        revisions = PrimaryBoto3ModelQuerySet(
            [
                DaemonRevision(daemonRevisionArn="daemon-revision-arn-1"),
                DaemonRevision(daemonRevisionArn="daemon-revision-arn-2"),
            ]
        )

        cluster_objects, cluster_manager = _manager_proxy("get", cluster)
        revision_objects, revision_manager = _manager_proxy("list", revisions)

        with patch.object(Cluster, "objects", cluster_objects):
            assert daemon.cluster is cluster

        with patch.object(DaemonRevision, "objects", revision_objects):
            assert daemon.current_revisions is revisions

        cluster_manager.get.assert_called_once_with(cluster="cluster-arn")
        revision_manager.list.assert_called_once_with(
            daemonRevisionArns=["daemon-revision-arn-1", "daemon-revision-arn-2"]
        )

    def test_daemon_revision_relations(self):
        session = MagicMock()
        revision = DaemonRevision(
            daemonRevisionArn="daemon-revision-arn-1",
            daemonArn="daemon-arn",
            clusterArn="cluster-arn",
            daemonTaskDefinitionArn="task-def-arn-1",
        )
        revision.set_session(session)
        daemon = Daemon(daemonArn="daemon-arn", clusterArn="cluster-arn")
        cluster = Cluster(clusterArn="cluster-arn", clusterName="cluster-name")
        task_definition = DaemonTaskDefinition(
            daemonTaskDefinitionArn="task-def-arn-1"
        )

        daemon_objects, daemon_manager = _manager_proxy("get", daemon)
        cluster_objects, cluster_manager = _manager_proxy("get", cluster)
        task_definition_objects, task_definition_manager = _manager_proxy(
            "get", task_definition
        )

        with (
            patch.object(Daemon, "objects", daemon_objects),
            patch.object(Cluster, "objects", cluster_objects),
            patch.object(DaemonTaskDefinition, "objects", task_definition_objects),
        ):
            assert revision.daemon is daemon
            assert revision.cluster is cluster
            assert revision.daemon_task_definition is task_definition

        daemon_manager.get.assert_called_once_with(daemonArn="daemon-arn")
        cluster_manager.get.assert_called_once_with(cluster="cluster-arn")
        task_definition_manager.get.assert_called_once_with(
            daemonTaskDefinition="task-def-arn-1"
        )

    def test_daemon_deployment_relations(self):
        session = MagicMock()
        deployment = DaemonDeployment(
            daemonDeploymentArn="deployment-arn",
            daemonArn="daemon-arn",
            clusterArn="cluster-arn",
            targetDaemonRevisionArn="daemon-revision-arn-1",
        )
        deployment.set_session(session)
        daemon = Daemon(daemonArn="daemon-arn", clusterArn="cluster-arn")
        cluster = Cluster(clusterArn="cluster-arn", clusterName="cluster-name")
        revision = DaemonRevision(daemonRevisionArn="daemon-revision-arn-1")

        daemon_objects, daemon_manager = _manager_proxy("get", daemon)
        cluster_objects, cluster_manager = _manager_proxy("get", cluster)
        revision_objects, revision_manager = _manager_proxy("get", revision)

        with (
            patch.object(Daemon, "objects", daemon_objects),
            patch.object(Cluster, "objects", cluster_objects),
            patch.object(DaemonRevision, "objects", revision_objects),
        ):
            assert deployment.daemon is daemon
            assert deployment.cluster is cluster
            assert deployment.target_revision is revision

        daemon_manager.get.assert_called_once_with(daemonArn="daemon-arn")
        cluster_manager.get.assert_called_once_with(cluster="cluster-arn")
        revision_manager.get.assert_called_once_with(
            daemonRevisionArn="daemon-revision-arn-1"
        )

    def test_express_gateway_service_relations(self):
        session = MagicMock()
        express_service = ExpressGatewayService(
            serviceArn="service-arn",
            serviceName="svc",
            cluster="cluster-arn",
            activeConfigurations=[
                {"serviceRevisionArn": "revision-arn-1"},
                {"serviceRevisionArn": "revision-arn-2"},
            ],
        )
        express_service.set_session(session)

        cluster = Cluster(clusterArn="cluster-arn", clusterName="cluster-name")
        service = Service(
            serviceName="svc",
            taskDefinition="family:1",
            clusterArn="cluster-arn",
            desiredCount=1,
            launchType="FARGATE",
            schedulingStrategy="REPLICA",
            serviceArn="service-arn",
        )
        revisions = PrimaryBoto3ModelQuerySet(
            [
                ServiceRevision(serviceRevisionArn="revision-arn-1"),
                ServiceRevision(serviceRevisionArn="revision-arn-2"),
            ]
        )

        cluster_objects, cluster_manager = _manager_proxy("get", cluster)
        service_objects, service_manager = _manager_proxy("get", service)
        revision_objects, revision_manager = _manager_proxy("list", revisions)

        with patch.object(Cluster, "objects", cluster_objects):
            assert express_service.cluster is cluster

        with patch.object(Service, "objects", service_objects):
            assert express_service.service is service

        with patch.object(ServiceRevision, "objects", revision_objects):
            assert express_service.active_service_revisions is revisions

        cluster_manager.get.assert_called_once_with(cluster="cluster-arn")
        service_manager.get.assert_called_once_with(
            service="service-arn",
            cluster="cluster-arn",
        )
        revision_manager.list.assert_called_once_with(
            serviceRevisionArns=["revision-arn-1", "revision-arn-2"]
        )
