from unittest.mock import MagicMock, patch

from botocraft.services.ecs import Cluster, ClusterManager, PrimaryBoto3ModelQuerySet


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
