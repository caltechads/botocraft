import json
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING

from botocraft.connectivity import (
    ConnectionResolutionError,
    TunnelAwareConnectionResolver,
)

if TYPE_CHECKING:
    import boto3

    from botocraft.connectivity import ResolvedConnectionTarget
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
    from botocraft.services.common import Credentials
    from botocraft.services.docdb import (
        ClusterMasterUserSecret,
        DocDBCluster,
        DocDBClusterParameterGroup,
        DocDBInstance,
        DocDBParameter,
        DocDBSubnetGroup,
    )

# ----------
# Decorators
# ----------


def single_docdb_cluster_include_tags(
    func: Callable[..., "DocDBCluster"],
) -> Callable[..., "DocDBCluster"]:
    """
    Decorator to convert a :py:class:`botocraft.services.docdb.DocDBCluster` object
    to a :py:class:`botocraft.services.docdb.DocDBCluster` object with tags included.

    Args:
        func: The manager method returning a single cluster.

    Returns:
        A wrapper that calls ``func`` and sets ``Tags`` on the returned
        cluster.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "DocDBCluster":
        response = func(self, *args, **kwargs)
        tags = self.client.list_tags_for_resource(ResourceName=response.DBClusterArn)
        response.Tags = tags["TagList"]
        return response

    return wrapper


def multiple_docdb_cluster_include_tags(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.docdb.DocDBCluster` objects to a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.docdb.DocDBCluster` objects with tags
    included.

    Args:
        func: The manager method returning a queryset of clusters.

    Returns:
        A wrapper that calls ``func`` and returns a new queryset whose
        clusters have ``Tags`` populated.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        response = func(self, *args, **kwargs)
        clusters: list[DocDBCluster] = []
        for cluster in response.all():
            tags = self.client.list_tags_for_resource(ResourceName=cluster.DBClusterArn)
            cluster.Tags = tags["TagList"]
            clusters.append(cluster)
        return PrimaryBoto3ModelQuerySet(clusters)

    return wrapper


def single_docdb_instance_include_tags(
    func: Callable[..., "DocDBInstance"],
) -> Callable[..., "DocDBInstance"]:
    """
    Decorator to convert a :py:class:`botocraft.services.docdb.DocDBInstance` object
    to a :py:class:`botocraft.services.docdb.DocDBInstance` object with tags included.

    Args:
        func: The manager method returning a single instance.

    Returns:
        A wrapper that calls ``func`` and sets ``Tags`` on the returned
        instance.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "DocDBInstance":
        response = func(self, *args, **kwargs)
        tags = self.client.list_tags_for_resource(ResourceName=response.DBInstanceArn)
        response.Tags = tags["TagList"]
        return response

    return wrapper


def multiple_docdb_instance_include_tags(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.docdb.DocDBInstance` objects to a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.docdb.DocDBInstance` objects with tags
    included.

    Args:
        func: The manager method returning a queryset of instances.

    Returns:
        A wrapper that calls ``func`` and returns a new queryset whose
        instances have ``Tags`` populated.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        response = func(self, *args, **kwargs)
        instances: list[DocDBInstance] = []
        for instance in response.all():
            tags = self.client.list_tags_for_resource(
                ResourceName=instance.DBInstanceArn
            )
            instance.Tags = tags["TagList"]
            instances.append(instance)
        return PrimaryBoto3ModelQuerySet(instances)

    return wrapper


def single_docdb_subnet_group_include_tags(
    func: Callable[..., "DocDBSubnetGroup"],
) -> Callable[..., "DocDBSubnetGroup"]:
    """
    Decorator to convert a :py:class:`botocraft.services.docdb.DocDBSubnetGroup`
    object to a :py:class:`botocraft.services.docdb.DocDBSubnetGroup` object
    with tags included.

    Args:
        func: The manager method returning a single subnet group.

    Returns:
        A wrapper that calls ``func`` and sets ``Tags`` on the returned
        subnet group.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "DocDBSubnetGroup":
        response = func(self, *args, **kwargs)
        tags = self.client.list_tags_for_resource(
            ResourceName=response.DBSubnetGroupArn
        )
        response.Tags = tags["TagList"]  # type: ignore[attr-defined]
        return response

    return wrapper


def multiple_docdb_subnet_group_include_tags(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.docdb.DocDBSubnetGroup` objects to a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.docdb.DocDBSubnetGroup` objects with tags
    included.

    Args:
        func: The manager method returning a queryset of subnet groups.

    Returns:
        A wrapper that calls ``func`` and returns a new queryset whose
        subnet groups have ``Tags`` populated.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        response = func(self, *args, **kwargs)
        subnet_groups: list[DocDBSubnetGroup] = []
        for subnet_group in response.all():
            tags = self.client.list_tags_for_resource(
                ResourceName=subnet_group.DBSubnetGroupArn
            )
            subnet_group.Tags = tags["TagList"]
            subnet_groups.append(subnet_group)
        return PrimaryBoto3ModelQuerySet(subnet_groups)

    return wrapper


def single_docdb_cluster_parameter_group_include_tags(
    func: Callable[..., "DocDBClusterParameterGroup"],
) -> Callable[..., "DocDBClusterParameterGroup"]:
    """
    Decorator that adds tags to a returned
    :py:class:`botocraft.services.docdb.DocDBClusterParameterGroup`.

    Args:
        func: The manager method returning a single parameter group.

    Returns:
        A wrapper that calls ``func`` and sets ``Tags`` on the returned
        parameter group.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "DocDBClusterParameterGroup":
        response = func(self, *args, **kwargs)
        tags = self.client.list_tags_for_resource(
            ResourceName=response.DBClusterParameterGroupArn
        )
        response.Tags = tags["TagList"]
        return response

    return wrapper


def multiple_docdb_cluster_parameter_group_include_tags(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorator to convert a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.docdb.DocDBClusterParameterGroup` objects to a
    :py:class:`botocraft.services.abstract.PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.docdb.DocDBClusterParameterGroup` objects with tags
    included.

    Args:
        func: The manager method returning a queryset of parameter groups.

    Returns:
        A wrapper that calls ``func`` and returns a new queryset whose
        cluster parameter groups have ``Tags`` populated.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        response = func(self, *args, **kwargs)
        parameter_groups: list[DocDBClusterParameterGroup] = []
        for parameter_group in response.all():
            tags = self.client.list_tags_for_resource(
                ResourceName=parameter_group.DBClusterParameterGroupArn
            )
            parameter_group.Tags = tags["TagList"]
            parameter_groups.append(parameter_group)
        return PrimaryBoto3ModelQuerySet(parameter_groups)

    return wrapper


# ----------
# Mixins
# ----------


class DocDBClusterParameterGroupManagerMixin:
    """
    A mixin for
    :py:class:`botocraft.services.docdb.DocDBClusterParameterGroupManager` that
    adds ``update``.

    ``ModifyDBClusterParameterGroup`` only returns the group name, so ``update``
    is written by hand to fetch and return the refreshed model instead.
    """

    def update(
        self,
        model: "DocDBClusterParameterGroup",
        Parameters: "list[DocDBParameter]",  # noqa: N803
    ) -> "DocDBClusterParameterGroup":
        """
        Modify the parameters of a cluster parameter group and return the group
        as it exists afterwards.

        A maximum of 20 parameters can be modified in a single request.

        Args:
            model: The :py:class:`DocDBClusterParameterGroup` to update.
            Parameters: The parameters to modify. Each needs ``ParameterName``,
                ``ParameterValue`` and ``ApplyMethod``.

        Returns:
            The refreshed :py:class:`DocDBClusterParameterGroup`, with tags.

        """
        self.client.modify_db_cluster_parameter_group(  # type: ignore[attr-defined]
            DBClusterParameterGroupName=model.DBClusterParameterGroupName,
            Parameters=self.serialize(Parameters),  # type: ignore[attr-defined]
        )
        return self.get(  # type: ignore[attr-defined]
            DBClusterParameterGroupName=model.DBClusterParameterGroupName
        )


class DocDBClusterModelMixin:
    """
    A mixin for :py:class:`botocraft.services.docdb.DocDBCluster` that adds
    some additional methods that we can't auto generate.
    """

    #: DocumentDB cluster identifier used in errors and connection labels.
    DBClusterIdentifier: str
    #: Cluster endpoint hostname.
    Endpoint: str | None
    #: Cluster endpoint port.
    Port: int | None
    #: Secret metadata for the master user credentials.
    MasterUserSecret: "ClusterMasterUserSecret | None"
    #: Boto3 session associated with this resource.
    session: "boto3.session.Session | None"

    @property
    def credentials(self) -> "Credentials":
        """
        Return the master user secret for the RDS instance.

        Raises:
            ValueError: If the RDS instance does not have a master user password
                in Secrets Manager.

        Returns:
            The master user secret for the RDS instance.

        """
        from botocraft.services.common import Credentials
        from botocraft.services.secretsmanager import Secret

        if not self.MasterUserSecret:
            msg = (
                f"DocumentDB instance {self.DBClusterIdentifier} does not have a "
                "master user password in Secrets Manager"
            )
            raise ValueError(msg)
        secret = Secret.objects.get(SecretId=self.MasterUserSecret.SecretArn)
        value = secret.get_value()
        data = json.loads(value.SecretString)
        return Credentials(username=data["username"], password=data["password"])

    def open_connection_target(
        self,
        *,
        profile: str | None = None,
    ) -> "ResolvedConnectionTarget":
        """
        Resolve a direct or tunneled connection target for the cluster.

        Keyword Args:
            profile: Optional AWS profile override forwarded to the tunnel host
                tunnel helper. Defaults to the active session profile when
                available.

        Raises:
            ConnectionResolutionError: The cluster does not expose a usable endpoint
                or VPC.

        Returns:
            Context-managed connection target for this DocumentDB cluster.

        """
        if not self.Endpoint or not self.Port:
            msg = (
                f"DocumentDB cluster '{self.DBClusterIdentifier}' does not have a "
                "usable endpoint."
            )
            raise ConnectionResolutionError(msg)

        vpc = getattr(self, "vpc", None)
        vpc_id = getattr(vpc, "VpcId", None)
        if not vpc_id:
            msg = (
                f"DocumentDB cluster '{self.DBClusterIdentifier}' does not have a "
                "resolvable VPC."
            )
            raise ConnectionResolutionError(msg)

        session = getattr(self, "session", None)
        resolved_profile = profile or getattr(session, "profile_name", None)
        resolver = TunnelAwareConnectionResolver()
        return resolver.open_connection_target(
            host=str(self.Endpoint),
            port=int(self.Port),
            vpc_id=str(vpc_id),
            session=session,
            profile=resolved_profile,
            resource_label=f"DocumentDB cluster '{self.DBClusterIdentifier}'",
        )
