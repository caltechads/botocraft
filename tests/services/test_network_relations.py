"""Tests for tunnel-related network relations on AWS resources."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

from botocraft.services.docdb import (
    DocDBCluster,
    DocDBSubnetGroup,
    DocDBSubnetGroupManager,
)
from botocraft.services.ec2 import (
    SecurityGroup,
    SecurityGroupManager,
    Subnet,
    SubnetManager,
    Vpc,
    VpcManager,
)
from botocraft.services.elasticache import (
    CacheCluster,
    CacheSubnetGroup,
    CacheSubnetGroupManager,
    ElastiCacheSubnet,
    ReplicationGroup,
    SecurityGroupMembership,
)
from botocraft.services.rds import (
    DBInstance,
    RDSDBSubnetGroup,
    RDSDBSubnetGroupManager,
    RDSSubnet,
)


class TestTunnelNetworkRelations:
    """Verify network helper relations used by tunnel resolution."""

    def test_cache_subnet_group_parses_elasticache_subnet_shape(self) -> None:
        """Accept ElastiCache subnet payloads that only expose subnet identifiers."""
        subnet_group = CacheSubnetGroup.model_validate(
            {
                "CacheSubnetGroupName": "cache-subnets",
                "CacheSubnetGroupDescription": "Cache subnet group",
                "VpcId": "vpc-123",
                "Subnets": [
                    {
                        "SubnetIdentifier": "subnet-1",
                        "SubnetAvailabilityZone": {"Name": "us-west-2a"},
                        "SubnetOutpost": {},
                        "SupportedNetworkTypes": ["ipv4"],
                    }
                ],
                "ARN": "arn:aws:elasticache:us-west-2:123456789012:subnetgroup:cache-subnets",
            }
        )

        assert subnet_group.Subnets[0].SubnetIdentifier == "subnet-1"

    def test_cache_cluster_network_relations(self) -> None:
        """Resolve ElastiCache cluster subnet group, VPC, subnets, and security groups."""
        cluster = CacheCluster(
            CacheClusterId="cache-main",
            CacheSubnetGroupName="cache-subnets",
            SecurityGroups=[SecurityGroupMembership.model_construct(SecurityGroupId="sg-1")],
            session=None,
        )
        subnet_group = cast("CacheSubnetGroup", object.__new__(CacheSubnetGroup))
        object.__setattr__(subnet_group, "CacheSubnetGroupName", "cache-subnets")
        object.__setattr__(subnet_group, "VpcId", "vpc-123")
        object.__setattr__(
            subnet_group,
            "Subnets",
            [cast("ElastiCacheSubnet", object.__new__(ElastiCacheSubnet))],
        )
        object.__setattr__(subnet_group.Subnets[0], "SubnetIdentifier", "subnet-1")
        object.__setattr__(subnet_group, "session", None)
        vpc = cast("Vpc", object.__new__(Vpc))
        object.__setattr__(vpc, "VpcId", "vpc-123")
        object.__setattr__(vpc, "session", None)
        subnets = [cast("Subnet", object.__new__(Subnet))]
        object.__setattr__(subnets[0], "SubnetId", "subnet-1")
        object.__setattr__(subnets[0], "session", None)
        security_groups = [
            cast("SecurityGroup", object.__new__(SecurityGroup))
        ]
        object.__setattr__(security_groups[0], "GroupId", "sg-1")
        object.__setattr__(security_groups[0], "GroupName", "app")
        object.__setattr__(security_groups[0], "session", None)

        with (
            patch.object(
                CacheSubnetGroupManager,
                "using",
                autospec=True,
                side_effect=lambda _self, _session: _self,
            ),
            patch.object(
                CacheSubnetGroupManager,
                "get",
                autospec=True,
                return_value=subnet_group,
            ) as get_subnet_group,
            patch.object(
                VpcManager,
                "using",
                autospec=True,
                side_effect=lambda _self, _session: _self,
            ),
            patch.object(
                VpcManager,
                "get",
                autospec=True,
                return_value=vpc,
            ) as get_vpc,
            patch.object(
                SubnetManager,
                "using",
                autospec=True,
                side_effect=lambda _self, _session: _self,
            ),
            patch.object(
                SubnetManager,
                "list",
                autospec=True,
                return_value=subnets,
            ) as list_subnets,
            patch.object(
                SecurityGroupManager,
                "using",
                autospec=True,
                side_effect=lambda _self, _session: _self,
            ),
            patch.object(
                SecurityGroupManager,
                "list",
                autospec=True,
                return_value=security_groups,
            ) as list_security_groups,
        ):
            related_subnet_group = cluster.subnet_group
            related_vpc = cluster.vpc
            related_subnets = cluster.subnets
            related_security_groups = cluster.security_groups

        get_subnet_group.assert_called_once()
        assert get_subnet_group.call_args.kwargs == {
            "CacheSubnetGroupName": "cache-subnets"
        }
        get_vpc.assert_called_once()
        assert get_vpc.call_args.kwargs == {"VpcId": "vpc-123"}
        list_subnets.assert_called_once()
        assert list_subnets.call_args.kwargs == {"SubnetIds": ["subnet-1"]}
        list_security_groups.assert_called_once()
        assert list_security_groups.call_args.kwargs == {"GroupIds": ["sg-1"]}
        assert related_subnet_group is subnet_group
        assert related_vpc is vpc
        assert related_subnets is subnets
        assert related_security_groups is security_groups

    def test_replication_group_network_helpers_fall_back_to_cluster(self) -> None:
        """Resolve replication-group network helpers through the first member cluster."""
        subnet_group = cast("CacheSubnetGroup", object.__new__(CacheSubnetGroup))
        object.__setattr__(subnet_group, "CacheSubnetGroupName", "cache-subnets")
        object.__setattr__(subnet_group, "VpcId", "vpc-123")
        object.__setattr__(subnet_group, "session", None)
        vpc = cast("Vpc", object.__new__(Vpc))
        object.__setattr__(vpc, "VpcId", "vpc-123")
        object.__setattr__(vpc, "session", None)
        subnets = [cast("Subnet", object.__new__(Subnet))]
        object.__setattr__(subnets[0], "SubnetId", "subnet-1")
        object.__setattr__(subnets[0], "session", None)
        security_groups = [
            cast("SecurityGroup", object.__new__(SecurityGroup))
        ]
        object.__setattr__(security_groups[0], "GroupId", "sg-1")
        object.__setattr__(security_groups[0], "GroupName", "app")
        object.__setattr__(security_groups[0], "session", None)
        cluster = SimpleNamespace(
            subnet_group=subnet_group,
            vpc=vpc,
            subnets=subnets,
            security_groups=security_groups,
        )
        replication_group = cast("ReplicationGroup", object.__new__(ReplicationGroup))
        object.__setattr__(replication_group, "ReplicationGroupId", "redis-main")
        object.__setattr__(replication_group, "MemberClusters", ["cache-main"])
        object.__setattr__(replication_group, "session", None)
        object.__setattr__(replication_group, "clusters", [cluster])

        assert replication_group.subnet_group is subnet_group
        assert replication_group.vpc is vpc
        assert replication_group.subnets is subnets
        assert replication_group.security_groups is security_groups

    def test_rds_instance_subnets_relation(self) -> None:
        """Resolve EC2 subnets from the instance subnet group."""
        instance = cast("DBInstance", object.__new__(DBInstance))
        object.__setattr__(instance, "DBInstanceIdentifier", "db-main")
        object.__setattr__(
            instance,
            "DBSubnetGroup",
            SimpleNamespace(DBSubnetGroupName="db-subnets", VpcId="vpc-123"),
        )
        object.__setattr__(instance, "session", None)
        subnet_group = cast("RDSDBSubnetGroup", object.__new__(RDSDBSubnetGroup))
        object.__setattr__(subnet_group, "DBSubnetGroupName", "db-subnets")
        object.__setattr__(subnet_group, "VpcId", "vpc-123")
        object.__setattr__(
            subnet_group,
            "Subnets",
            [cast("RDSSubnet", object.__new__(RDSSubnet))],
        )
        object.__setattr__(subnet_group.Subnets[0], "SubnetIdentifier", "subnet-1")
        object.__setattr__(subnet_group, "session", None)
        subnets = [cast("Subnet", object.__new__(Subnet))]
        object.__setattr__(subnets[0], "SubnetId", "subnet-1")
        object.__setattr__(subnets[0], "session", None)

        with (
            patch.object(
                RDSDBSubnetGroupManager,
                "using",
                autospec=True,
                side_effect=lambda _self, _session: _self,
            ),
            patch.object(
                RDSDBSubnetGroupManager,
                "get",
                autospec=True,
                return_value=subnet_group,
            ),
            patch.object(
                SubnetManager,
                "using",
                autospec=True,
                side_effect=lambda _self, _session: _self,
            ),
            patch.object(
                SubnetManager,
                "list",
                autospec=True,
                return_value=subnets,
            ) as list_subnets,
        ):
            related_subnets = instance.subnets

        list_subnets.assert_called_once()
        assert list_subnets.call_args.kwargs == {"SubnetIds": ["subnet-1"]}
        assert related_subnets is subnets

    def test_docdb_cluster_subnets_relation(self) -> None:
        """Resolve EC2 subnets from the DocumentDB cluster subnet group."""
        cluster = cast("DocDBCluster", object.__new__(DocDBCluster))
        object.__setattr__(cluster, "DBClusterIdentifier", "docdb-main")
        object.__setattr__(cluster, "DBSubnetGroup", "docdb-subnets")
        object.__setattr__(cluster, "session", None)
        subnet_group = cast("DocDBSubnetGroup", object.__new__(DocDBSubnetGroup))
        object.__setattr__(subnet_group, "DBSubnetGroupName", "docdb-subnets")
        object.__setattr__(subnet_group, "VpcId", "vpc-123")
        object.__setattr__(
            subnet_group,
            "Subnets",
            [SimpleNamespace(SubnetIdentifier="subnet-1")],
        )
        object.__setattr__(subnet_group, "session", None)
        subnets = [cast("Subnet", object.__new__(Subnet))]
        object.__setattr__(subnets[0], "SubnetId", "subnet-1")
        object.__setattr__(subnets[0], "session", None)

        with (
            patch.object(
                DocDBSubnetGroupManager,
                "using",
                autospec=True,
                side_effect=lambda _self, _session: _self,
            ),
            patch.object(
                DocDBSubnetGroupManager,
                "get",
                autospec=True,
                return_value=subnet_group,
            ),
            patch.object(
                SubnetManager,
                "using",
                autospec=True,
                side_effect=lambda _self, _session: _self,
            ),
            patch.object(
                SubnetManager,
                "list",
                autospec=True,
                return_value=subnets,
            ) as list_subnets,
        ):
            related_subnets = cluster.subnets

        list_subnets.assert_called_once()
        assert list_subnets.call_args.kwargs == {"SubnetIds": ["subnet-1"]}
        assert related_subnets is subnets
