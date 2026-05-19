from collections.abc import Callable
from functools import cached_property, wraps
from typing import TYPE_CHECKING, cast

import boto3

from botocraft.connectivity import (
    ConnectionResolutionError,
    TunnelAwareConnectionResolver,
)
from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.connectivity import ResolvedConnectionTarget
    from botocraft.services import CacheSecurityGroupMembership
    from botocraft.services.elasticache import (
        CacheNode,
        CacheSubnetGroup,
        NodeGroup,
    )

# ------------
# Decorators
# ------------


def elasticache_user_add_tags(func: Callable) -> Callable:
    """
    A decorator to add tags to the elasticache user.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        tags = self.objects.client.list_tags_for_resource(ResourceName=result.arn)
        result.Tags = tags["Tags"]
        return result

    return wrapper


def elasticache_users_get_add_tags(func: Callable) -> Callable:
    """
    A decorator to add tags to the elasticache users.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        for user in result:
            tags = self.objects.client.list_tags_for_resource(ResourceName=user.Arn)
            user.Tags = tags["Tags"]
        return PrimaryBoto3ModelQuerySet(result)

    return wrapper


def elasticache_user_group_add_tags(func: Callable) -> Callable:
    """
    A decorator to add tags to the elasticache user group.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        tags = self.objects.client.list_tags_for_resource(ResourceName=result.arn)
        result.Tags = tags["Tags"]
        return result

    return wrapper


def elasticache_user_groups_get_add_tags(func: Callable) -> Callable:
    """
    A decorator to add tags to the elasticache user groups.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        for user_group in result:
            tags = self.objects.client.list_tags_for_resource(
                ResourceName=user_group.arn
            )
            user_group.Tags = tags["Tags"]
        return PrimaryBoto3ModelQuerySet(result)

    return wrapper


# -----------
# Mixins
# ----------


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

    #: Boto3 session associated with this resource.
    session: boto3.session.Session
    #: Security-group memberships returned by ElastiCache.
    CacheSecurityGroups: list["CacheSecurityGroupMembership"]
    #: Cache-cluster identifier used in errors and connection labels.
    CacheClusterId: str
    #: Cache nodes used to resolve the endpoint host and port.
    CacheNodes: list["CacheNode"]
    #: Related subnet group used to resolve the target VPC.
    subnet_group: "CacheSubnetGroup | None"

    @property
    def security_groups(self) -> "PrimaryBoto3ModelQuerySet":
        """
        List all the :py:class:`CacheCluster` objects that are part of this
        replication group.
        """
        # We have to do the actual import here to avoid circular imports
        from botocraft.services import CacheSecurityGroup

        names = [x.CacheSecurityGroupName for x in self.CacheSecurityGroups]
        return PrimaryBoto3ModelQuerySet(
            [
                CacheSecurityGroup.objects.using(self.session).get(group_name)
                for group_name in names
            ]
        )  # type: ignore[arg-type]

    @cached_property
    def hostname(self) -> str:
        """
        The hostname of the cache cluster.

        Note:
            This is the hostname of the first node in the cluster.  If you have
            a cluster with multiple nodes, you will need to use the ``CacheNodes``
            property to get the hostnames of the other nodes.

        """
        endpoint = self.CacheNodes[0].Endpoint
        if endpoint is None or endpoint.Address is None:
            msg = (
                f"ElastiCache cache cluster '{self.CacheClusterId}' does not have a "
                "usable endpoint."
            )
            raise ConnectionResolutionError(msg)
        return endpoint.Address

    @cached_property
    def port(self) -> int:
        """
        The port of the cache cluster.

        Note:
            This is the port of the first node in the cluster.  If you have
            a cluster with multiple nodes, you will need to use the ``CacheNodes``
            property to get the ports of the other nodes.

        """
        endpoint = self.CacheNodes[0].Endpoint
        if endpoint is None or endpoint.Port is None:
            msg = (
                f"ElastiCache cache cluster '{self.CacheClusterId}' does not have a "
                "usable endpoint."
            )
            raise ConnectionResolutionError(msg)
        return endpoint.Port

    @cached_property
    def tags(self) -> dict[str, str]:
        """
        Get the tags for the cache cluster.

        This is a dictionary of key/value pairs, where the key is the tag name
        and the value is the tag value
        """
        return self.objects.using(self.session).get_tags(self.arn)  # type: ignore[attr-defined]

    def open_connection_target(
        self,
        *,
        profile: str | None = None,
    ) -> "ResolvedConnectionTarget":
        """
        Resolve a direct or tunneled connection target for the cache cluster.

        Keyword Args:
            profile: Optional AWS profile override forwarded to the provisioner
                tunnel helper. Defaults to the active session profile when
                available.

        Raises:
            ConnectionResolutionError: The cache cluster does not resolve to a
                usable VPC.

        Returns:
            Context-managed connection target for this cache cluster.

        """
        if not getattr(self, "CacheNodes", None):
            msg = (
                f"ElastiCache cache cluster '{self.CacheClusterId}' does not have a "
                "usable endpoint."
            )
            raise ConnectionResolutionError(msg)

        subnet_group = getattr(self, "subnet_group", None)
        vpc_id = getattr(subnet_group, "VpcId", None)
        if not vpc_id:
            msg = (
                f"ElastiCache cache cluster '{self.CacheClusterId}' does not have a "
                "resolvable VPC."
            )
            raise ConnectionResolutionError(msg)

        session = getattr(self, "session", None)
        resolved_profile = profile or getattr(session, "profile_name", None)
        resolver = TunnelAwareConnectionResolver()
        return resolver.open_connection_target(
            host=self.hostname,
            port=self.port,
            vpc_id=str(vpc_id),
            session=session,
            profile=resolved_profile,
            resource_label=f"ElastiCache cache cluster '{self.CacheClusterId}'",
        )


class ReplicationGroupModelMixin:
    """
    A mixin is used on :py:class:`botocraft.services.elasticache.ReplicationGroup`
    implement the "clusters" relation.   Normally we would use a "relation" type
    in the model definition to use the .list() function to list what we want, but
    ``describe_cache_clusters`` either lists a single cluster or all clusters,
    so we need to roll our own method
    """

    #: Boto3 session associated with this resource.
    session: boto3.session.Session
    #: Cache-cluster identifiers that belong to this replication group.
    MemberClusters: list[str]
    #: Replication-group identifier used in errors and connection labels.
    ReplicationGroupId: str
    #: Node groups used to resolve the primary endpoint host and port.
    NodeGroups: list["NodeGroup"]

    @cached_property
    def clusters(self) -> "PrimaryBoto3ModelQuerySet":
        """
        List all the :py:class:`CacheCluster` objects that are part of this
        replication group.
        """
        # We have to do the actual import here to avoid circular imports
        from botocraft.services import CacheCluster

        return PrimaryBoto3ModelQuerySet(
            [
                CacheCluster.objects.using(self.session).get(cluster_id)
                for cluster_id in self.MemberClusters
            ]
        )  # type: ignore[arg-type]

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
        endpoint = self.NodeGroups[0].PrimaryEndpoint
        if endpoint is None or endpoint.Address is None:
            msg = (
                f"ElastiCache replication group '{self.ReplicationGroupId}' does not "
                "have a usable endpoint."
            )
            raise ConnectionResolutionError(msg)
        return endpoint.Address

    @cached_property
    def port(self) -> int:
        """
        The port of the cache cluster.
        """
        endpoint = self.NodeGroups[0].PrimaryEndpoint
        if endpoint is None or endpoint.Port is None:
            msg = (
                f"ElastiCache replication group '{self.ReplicationGroupId}' does not "
                "have a usable endpoint."
            )
            raise ConnectionResolutionError(msg)
        return endpoint.Port

    @cached_property
    def tags(self) -> dict[str, str]:
        """
        Get the tags for the replication group.

        This is a dictionary of key/value pairs, where the key is the tag name
        and the value is the tag value
        """
        return self.objects.using(self.session).get_tags(self.arn)  # type: ignore[attr-defined]

    def open_connection_target(
        self,
        *,
        profile: str | None = None,
    ) -> "ResolvedConnectionTarget":
        """
        Resolve a direct or tunneled connection target for the replication group.

        Keyword Args:
            profile: Optional AWS profile override forwarded to the provisioner
                tunnel helper. Defaults to the active session profile when
                available.

        Raises:
            ConnectionResolutionError: The replication group does not resolve to a
                usable VPC.

        Returns:
            Context-managed connection target for this replication group.

        """
        if not getattr(self, "NodeGroups", None):
            msg = (
                f"ElastiCache replication group '{self.ReplicationGroupId}' does "
                "not have a usable endpoint."
            )
            raise ConnectionResolutionError(msg)

        vpc_id = None
        if getattr(self, "clusters", None):
            vpc = getattr(self.clusters[0], "vpc", None)
            vpc_id = getattr(vpc, "VpcId", None)
        if not vpc_id:
            msg = (
                f"ElastiCache replication group '{self.ReplicationGroupId}' does not "
                "have a resolvable VPC."
            )
            raise ConnectionResolutionError(msg)

        session = getattr(self, "session", None)
        resolved_profile = profile or getattr(session, "profile_name", None)
        resolver = TunnelAwareConnectionResolver()
        return resolver.open_connection_target(
            host=self.hostname,
            port=self.port,
            vpc_id=str(vpc_id),
            session=session,
            profile=resolved_profile,
            resource_label=(
                f"ElastiCache replication group '{self.ReplicationGroupId}'"
            ),
        )
