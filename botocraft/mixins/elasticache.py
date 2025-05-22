from functools import cached_property
from typing import TYPE_CHECKING, List, cast

import boto3

if TYPE_CHECKING:
    from botocraft.services import (
        CacheCluster,
        CacheSecurityGroup,
        CacheSecurityGroupMembership,
    )


class ElastiCacheManagerTagsMixin:
    """
    Used on both :py:class:`botocraft.services.elasticache.CacheCluster` and
    :py:class:`botocraft.services.elasticache.ReplicationGroup` to implement the
    ``tags`` relation.
    """

    def get_tags(self, arn: str) -> dict[str, str]:
        """
        Get the tags for the elasticache resource identified by ``arn``.

        Args:
            arn: The ARN of the elasticache resource

        Returns:
            A dictionary of key/value pairs, where the key is the tag name and
            the value is the tag value

        """
        tags = self.client.list_tags_for_resource(ResourceName=arn)["TagList"]  # type: ignore[attr-defined]
        # Convert the list of tags to a dictionary
        _tags: dict[str, str] = {}
        for tag in tags:
            _tags[tag["Key"]] = tag["Value"]
        return _tags


class CacheClusterModelMixin:
    """
    A mixin is used on :py:class:`botocraft.services.elasticache.CacheCluster`
    implement the "security_groups" relation.   Normally we would use a
    "relation" type in the model definition to use the .list() function to list
    what we want, but ``describe_cache_clusters`` either lists a single cluster
    or all clusters, so we need to roll our own method
    """

    session: boto3.session.Session
    CacheSecurityGroups: List["CacheSecurityGroupMembership"]

    @property
    def security_groups(self) -> List["CacheSecurityGroup"]:
        """
        List all the :py:class:`CacheCluster` objects that are part of this
        replication group.
        """
        # We have to do the actual import here to avoid circular imports
        from botocraft.services import CacheSecurityGroup

        names = [x.CacheSecurityGroupName for x in self.CacheSecurityGroups]
        return [
            CacheSecurityGroup.objects.using(self.session).get(group_name)
            for group_name in names
        ]

    @cached_property
    def hostname(self) -> str:
        """
        The hostname of the cache cluster.

        Note:
            This is the hostname of the first node in the cluster.  If you have
            a cluster with multiple nodes, you will need to use the ``CacheNodes``
            property to get the hostnames of the other nodes.

        """
        return cast("str", self.CacheNodes[0].Endpoint.Address)  # type: ignore[attr-defined]

    @cached_property
    def port(self) -> int:
        """
        The port of the cache cluster.

        Note:
            This is the port of the first node in the cluster.  If you have
            a cluster with multiple nodes, you will need to use the ``CacheNodes``
            property to get the ports of the other nodes.

        """
        return cast("int", self.CacheNodes[0].Endpoint.Port)  # type: ignore[attr-defined]

    @cached_property
    def tags(self) -> dict[str, str]:
        """
        Get the tags for the cache cluster.

        This is a dictionary of key/value pairs, where the key is the tag name
        and the value is the tag value
        """
        return self.objects.using(self.session).get_tags(self.arn)  # type: ignore[attr-defined]


class ReplicationGroupModelMixin:
    """
    A mixin is used on :py:class:`botocraft.services.elasticache.ReplicationGroup`
    implement the "clusters" relation.   Normally we would use a "relation" type
    in the model definition to use the .list() function to list what we want, but
    ``describe_cache_clusters`` either lists a single cluster or all clusters,
    so we need to roll our own method
    """

    session: boto3.session.Session
    MemberClusters: List[str]

    @cached_property
    def clusters(self) -> List["CacheCluster"]:
        """
        List all the :py:class:`CacheCluster` objects that are part of this
        replication group.
        """
        # We have to do the actual import here to avoid circular imports
        from botocraft.services import CacheCluster

        return [
            CacheCluster.objects.using(self.session).get(cluster_id)
            for cluster_id in self.MemberClusters
        ]

    @property
    def engine_version(self) -> str:
        """
        The engine version of the replication group.  This is the same as the
        engine version of the first cluster in the replication group.
        """
        from botocraft.services import CacheCluster

        cluster = CacheCluster.objects.using(self.session).get(
            self.MemberClusters[0], ShowCacheNodeInfo=False
        )
        return cast("str", cluster.EngineVersion)

    @cached_property
    def hostname(self) -> str:
        """
        The hostname of the cache cluster.
        """
        return cast("str", self.NodeGroups[0].PrimaryEndpoint.Address)  # type: ignore[attr-defined]

    @cached_property
    def port(self) -> int:
        """
        The port of the cache cluster.
        """
        return cast("int", self.NodeGroups[0].PrimaryEndpoint.Port)  # type: ignore[attr-defined]

    @cached_property
    def tags(self) -> dict[str, str]:
        """
        Get the tags for the replication group.

        This is a dictionary of key/value pairs, where the key is the tag name
        and the value is the tag value
        """
        return self.objects.using(self.session).get_tags(self.arn)  # type: ignore[attr-defined]
