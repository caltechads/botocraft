from __future__ import annotations

from functools import cached_property

from botocraft.eventbridge.common import first_resource


class SearchServiceDomainEvent:
    """
    Shared conveniences for ``aws.es`` EventBridge wrappers.
    """

    #: EventBridge resource ARNs attached by raw event models.
    resources: list[str]

    @property
    def domain_arn(self) -> str | None:
        """
        Return first domain ARN referenced by event resources.

        Returns:
            First resource ARN when present, otherwise ``None``.

        """
        return first_resource(self.resources)

    @property
    def domain_name(self) -> str | None:
        """
        Return domain name parsed from first resource ARN.

        Returns:
            Domain name when a domain ARN is present, otherwise ``None``.

        """
        if not self.domain_arn:
            return None
        return self.domain_arn.rsplit("/", maxsplit=1)[-1]

    @cached_property
    def domain(self):  # type: ignore[no-untyped-def]
        """
        Return related OpenSearch domain object when session is available.

        Returns:
            Matching ``OpenSearchDomain`` when the event names one, otherwise
            ``None``.

        """
        if not self.domain_name or self.session is None:
            return None

        from botocraft.services.opensearch import OpenSearchDomain

        return OpenSearchDomain.objects.using(self.session).get(self.domain_name)
