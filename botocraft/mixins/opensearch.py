from collections.abc import Callable
from functools import cached_property, wraps
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

from botocraft.connectivity import (
    ConnectionResolutionError,
    TunnelAwareConnectionResolver,
)

if TYPE_CHECKING:
    import boto3

    from botocraft.connectivity import ResolvedConnectionTarget
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
    from botocraft.services.opensearch import OpenSearchDomain, OpenSearchPackage


# ----------
# Decorators
# ----------


def _attach_domain_tags(
    client: object, domain: "OpenSearchDomain"
) -> "OpenSearchDomain":
    tags = client.list_tags(ARN=domain.ARN)  # type: ignore[attr-defined]
    domain.Tags = tags["TagList"]
    return domain


def single_opensearch_domain_include_tags(
    func: Callable[..., "OpenSearchDomain"],
) -> Callable[..., "OpenSearchDomain"]:
    """
    Decorate a manager method so the returned domain includes tags.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "OpenSearchDomain":
        response = func(self, *args, **kwargs)
        return _attach_domain_tags(self.client, response)

    return wrapper


def multiple_opensearch_domains_include_tags(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Decorate a manager method so listed domains include tags.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        response = func(self, *args, **kwargs)
        domains = [
            _attach_domain_tags(self.client, cast("OpenSearchDomain", domain))
            for domain in response.all()
        ]
        from botocraft.services.abstract import Boto3Model

        return PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", domains))

    return wrapper


def single_opensearch_domain_update_include_tags(
    func: Callable[..., object],
) -> Callable[..., "OpenSearchDomain"]:
    """
    Decorate domain updates so the returned domain is re-described with tags.
    """

    @wraps(func)
    def wrapper(
        self, domain: "OpenSearchDomain", *args, **kwargs
    ) -> "OpenSearchDomain":
        func(self, domain, *args, **kwargs)
        refreshed = self.get(DomainName=domain.DomainName)
        return _attach_domain_tags(self.client, refreshed)

    return wrapper


# ----------
# Mixins
# ----------


class OpenSearchDomainManagerMixin:
    """
    Manager helpers for :py:class:`botocraft.services.opensearch.OpenSearchDomain`.

    Amazon OpenSearch Service uses ``list_domain_names`` to enumerate domains and
    ``describe_domains`` to hydrate them, so the generated ``describe_domains`` list
    method cannot support the normal zero-argument Botocraft contract on its own.
    """

    #: Boto3 client used by the generated manager.
    client: object

    def list(
        self,
        *,
        EngineType: str | None = None,  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet":
        """
        Return OpenSearch domains visible to the current session.

        Keyword Args:
            EngineType: Optional engine family filter forwarded to
                ``list_domain_names``.

        Returns:
            A queryset of :py:class:`botocraft.services.opensearch.OpenSearchDomain`
            objects.

        """
        from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet
        from botocraft.services.opensearch import OpenSearchDomain

        args: dict[str, Any] = {
            "EngineType": self.serialize(EngineType),  # type: ignore[attr-defined]
        }
        response = self.client.list_domain_names(  # type: ignore[attr-defined]
            **{key: value for key, value in args.items() if value is not None}
        )
        names = [
            item["DomainName"]
            for item in response.get("DomainNames", [])
            if item.get("DomainName")
        ]
        if not names:
            return PrimaryBoto3ModelQuerySet([])

        described = self.client.describe_domains(  # type: ignore[attr-defined]
            DomainNames=names,
        )
        domains = [
            _attach_domain_tags(self.client, OpenSearchDomain(**payload))
            for payload in described.get("DomainStatusList", [])
        ]
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", domains))
        self.sessionize(query_set)  # type: ignore[attr-defined]
        return query_set


class OpenSearchPackageManagerMixin:
    """
    Manager helpers for :py:class:`botocraft.services.opensearch.Package`.
    """

    #: Boto3 client used by the generated manager.
    client: object

    def get(self, PackageID: str) -> "OpenSearchPackage":  # noqa: N803
        """
        Return a single package by ID.

        Args:
            PackageID: The package identifier.

        Raises:
            ValueError: No package exists for the given ID.

        Returns:
            The matching package.

        """
        from botocraft.services.opensearch import OpenSearchPackage

        response = self.client.describe_packages(  # type: ignore[attr-defined]
            Filters=[{"Name": "PackageID", "Value": [PackageID]}],
        )
        packages = response.get("PackageDetailsList") or []
        if not packages:
            msg = f"OpenSearch package '{PackageID}' was not found."
            raise ValueError(msg)
        package = OpenSearchPackage.model_validate(packages[0])
        self.sessionize(package)  # type: ignore[attr-defined]
        return package


class DomainModelMixin:
    """
    Convenience helpers for :py:class:`botocraft.services.opensearch.OpenSearchDomain`.
    """

    #: OpenSearch domain name used in errors and connection labels.
    DomainName: str
    #: Primary service endpoint URL.
    Endpoint: str | None
    #: Secondary service endpoint URL.
    EndpointV2: str | None
    #: Boto3 session associated with this resource.
    session: "boto3.session.Session | None"

    @cached_property
    def hostname(self) -> str:
        """
        Return the hostname for the domain endpoint.

        Raises:
            ConnectionResolutionError: The domain does not expose a usable endpoint.

        Returns:
            The domain endpoint hostname.

        """
        endpoint = self.EndpointV2 or self.Endpoint
        if not endpoint:
            msg = (
                f"OpenSearch domain '{self.DomainName}' does not have a usable "
                "endpoint."
            )
            raise ConnectionResolutionError(msg)

        parsed = urlparse(
            endpoint if "://" in endpoint else f"https://{endpoint}",
        )
        if not parsed.hostname:
            msg = (
                f"OpenSearch domain '{self.DomainName}' does not have a usable "
                "endpoint."
            )
            raise ConnectionResolutionError(msg)
        return parsed.hostname

    @cached_property
    def port(self) -> int:
        """
        Return the port for the domain endpoint.

        Raises:
            ConnectionResolutionError: The domain does not expose a usable endpoint.

        Returns:
            The domain endpoint port.

        """
        endpoint = self.EndpointV2 or self.Endpoint
        if not endpoint:
            msg = (
                f"OpenSearch domain '{self.DomainName}' does not have a usable "
                "endpoint."
            )
            raise ConnectionResolutionError(msg)

        parsed = urlparse(
            endpoint if "://" in endpoint else f"https://{endpoint}",
        )
        if parsed.port is not None:
            return parsed.port
        if parsed.scheme == "http":
            return 80
        return 443

    def open_connection_target(
        self,
        *,
        profile: str | None = None,
    ) -> "ResolvedConnectionTarget":
        """
        Resolve a direct or tunneled connection target for the domain.

        Keyword Args:
            profile: Optional AWS profile override forwarded to the tunnel host
                tunnel helper. Defaults to the active session profile when
                available.

        Raises:
            ConnectionResolutionError: The domain does not expose a usable endpoint
                or VPC.

        Returns:
            Context-managed connection target for this OpenSearch domain.

        """
        vpc = getattr(self, "vpc", None)
        vpc_id = getattr(vpc, "VpcId", None)
        if not vpc_id:
            msg = (
                f"OpenSearch domain '{self.DomainName}' does not have a resolvable VPC."
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
            resource_label=f"OpenSearch domain '{self.DomainName}'",
        )
