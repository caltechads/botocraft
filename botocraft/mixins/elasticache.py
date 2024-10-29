from typing import TYPE_CHECKING, List

import boto3

if TYPE_CHECKING:
    from botocraft.services import (
        CacheCluster,
        CacheSecurityGroup,
        CacheSecurityGroupMembership,
    )


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

    @property
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
