"""Tests for resource mixins that expose tunnel-aware connection targets."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import ANY, Mock, patch

import pytest

from botocraft.connectivity import ConnectionResolutionError
from botocraft.services.docdb import DocDBCluster
from botocraft.services.elasticache import CacheCluster, ReplicationGroup
from botocraft.services.rds import DBInstance


class TestConnectionTargets:
    """Verify resource mixins delegate to the shared resolver."""

    def test_rds_instance_open_connection_target(self) -> None:
        """Resolve RDS host, port, VPC, and label through the shared resolver."""
        resolver = Mock()
        resolver.open_connection_target.return_value = object()
        instance = cast("DBInstance", object.__new__(DBInstance))
        object.__setattr__(instance, "DBInstanceIdentifier", "db-main")
        object.__setattr__(
            instance,
            "Endpoint",
            SimpleNamespace(Address="db.example", Port=3306),
        )
        object.__setattr__(instance, "vpc", SimpleNamespace(VpcId="vpc-123"))
        object.__setattr__(instance, "session", SimpleNamespace(profile_name="dev"))

        with patch(
            "botocraft.mixins.rds.TunnelAwareConnectionResolver",
            return_value=resolver,
        ):
            result = instance.open_connection_target()

        assert result is resolver.open_connection_target.return_value
        resolver.open_connection_target.assert_called_once_with(
            host="db.example",
            port=3306,
            vpc_id="vpc-123",
            session=ANY,
            profile="dev",
            resource_label="RDS instance 'db-main'",
        )

    def test_cache_cluster_open_connection_target(self) -> None:
        """Resolve ElastiCache cluster host, port, VPC, and label."""
        resolver = Mock()
        resolver.open_connection_target.return_value = object()
        cluster = cast("CacheCluster", object.__new__(CacheCluster))
        object.__setattr__(cluster, "CacheClusterId", "cache-main")
        object.__setattr__(
            cluster,
            "CacheNodes",
            [
                SimpleNamespace(
                    Endpoint=SimpleNamespace(Address="cache.example", Port=6379)
                )
            ],
        )
        object.__setattr__(cluster, "vpc", SimpleNamespace(VpcId="vpc-456"))
        object.__setattr__(cluster, "session", SimpleNamespace(profile_name="dev"))

        with patch(
            "botocraft.mixins.elasticache.TunnelAwareConnectionResolver",
            return_value=resolver,
        ):
            result = cluster.open_connection_target()

        assert result is resolver.open_connection_target.return_value
        resolver.open_connection_target.assert_called_once_with(
            host="cache.example",
            port=6379,
            vpc_id="vpc-456",
            session=ANY,
            profile="dev",
            resource_label="ElastiCache cache cluster 'cache-main'",
        )

    def test_replication_group_open_connection_target(self) -> None:
        """Resolve ElastiCache replication-group host, port, VPC, and label."""
        resolver = Mock()
        resolver.open_connection_target.return_value = object()
        replication_group = cast(
            "ReplicationGroup",
            object.__new__(ReplicationGroup),
        )
        object.__setattr__(replication_group, "ReplicationGroupId", "redis-main")
        object.__setattr__(
            replication_group,
            "NodeGroups",
            [
                SimpleNamespace(
                    PrimaryEndpoint=SimpleNamespace(
                        Address="redis.example",
                        Port=6379,
                    )
                )
            ],
        )
        object.__setattr__(replication_group, "vpc", SimpleNamespace(VpcId="vpc-789"))
        object.__setattr__(
            replication_group,
            "session",
            SimpleNamespace(profile_name="dev"),
        )

        with patch(
            "botocraft.mixins.elasticache.TunnelAwareConnectionResolver",
            return_value=resolver,
        ):
            result = replication_group.open_connection_target()

        assert result is resolver.open_connection_target.return_value
        resolver.open_connection_target.assert_called_once_with(
            host="redis.example",
            port=6379,
            vpc_id="vpc-789",
            session=ANY,
            profile="dev",
            resource_label="ElastiCache replication group 'redis-main'",
        )

    def test_docdb_cluster_open_connection_target(self) -> None:
        """Resolve DocumentDB host, port, VPC, and label."""
        resolver = Mock()
        resolver.open_connection_target.return_value = object()
        cluster = cast("DocDBCluster", object.__new__(DocDBCluster))
        object.__setattr__(cluster, "DBClusterIdentifier", "docdb-main")
        object.__setattr__(cluster, "Endpoint", "docdb.example")
        object.__setattr__(cluster, "Port", 27017)
        object.__setattr__(cluster, "vpc", SimpleNamespace(VpcId="vpc-321"))
        object.__setattr__(cluster, "session", SimpleNamespace(profile_name="dev"))

        with patch(
            "botocraft.mixins.docdb.TunnelAwareConnectionResolver",
            return_value=resolver,
        ):
            result = cluster.open_connection_target()

        assert result is resolver.open_connection_target.return_value
        resolver.open_connection_target.assert_called_once_with(
            host="docdb.example",
            port=27017,
            vpc_id="vpc-321",
            session=ANY,
            profile="dev",
            resource_label="DocumentDB cluster 'docdb-main'",
        )

    def test_cache_cluster_raises_for_missing_endpoint(self) -> None:
        """Raise a clear error when a cache cluster has no usable endpoint."""
        cluster = cast("CacheCluster", object.__new__(CacheCluster))
        object.__setattr__(cluster, "CacheClusterId", "cache-main")
        object.__setattr__(cluster, "CacheNodes", [])
        object.__setattr__(cluster, "vpc", SimpleNamespace(VpcId="vpc-456"))
        object.__setattr__(cluster, "session", SimpleNamespace(profile_name="dev"))

        with pytest.raises(ConnectionResolutionError, match="usable endpoint"):
            cluster.open_connection_target()

    def test_replication_group_raises_for_missing_endpoint(self) -> None:
        """Raise a clear error when a replication group has no usable endpoint."""
        replication_group = cast(
            "ReplicationGroup",
            object.__new__(ReplicationGroup),
        )
        object.__setattr__(replication_group, "ReplicationGroupId", "redis-main")
        object.__setattr__(replication_group, "NodeGroups", [])
        object.__setattr__(replication_group, "vpc", SimpleNamespace(VpcId="vpc-789"))
        object.__setattr__(
            replication_group,
            "session",
            SimpleNamespace(profile_name="dev"),
        )

        with pytest.raises(ConnectionResolutionError, match="usable endpoint"):
            replication_group.open_connection_target()
