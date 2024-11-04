from typing import TYPE_CHECKING, Literal, Optional

import boto3

if TYPE_CHECKING:
    from botocraft.services import (
        Route53ResourceRecordSet,
    )

Route53RecordType = Literal[
    "SOA",
    "A",
    "TXT",
    "NS",
    "CNAME",
    "MX",
    "NAPTR",
    "PTR",
    "SRV",
    "SPF",
    "AAAA",
    "CAA",
    "DS",
]


class HostedZoneModelMixin:
    """
    A mixin is used on :py:class:`botocraft.services.route53.HostedZone`
    implement the "lookup" relation.   Normally we would use a
    "relation" type in the model definition to use the .list() function to list
    what we want, but ``describe_cache_clusters`` either lists a single cluster
    or all clusters, so we need to roll our own method
    """

    session: boto3.session.Session
    Id: str

    def lookup(
        self,
        RecordName: str,  # noqa: N803
        RecordType: Route53RecordType = "A",  # noqa: N803
    ) -> Optional["Route53ResourceRecordSet"]:
        """
        Look for a record in this hosted zone with the given name and type.

        Args:
            RecordName: The name of the record to look up.

        Keyword Args:
            RecordType: The type of record to look up.  Defaults to "A".

        Returns:
            The record if found, or None if not found.

        """
        # We have to do the actual import here to avoid circular imports
        from botocraft.services import Route53ResourceRecordSet

        records = Route53ResourceRecordSet.objects.using(self.session).list(
            HostedZoneId=self.Id,
            StartRecordName=RecordName,
            StartRecordType=RecordType,
            MaxItems="1",
        )
        if not records:
            return None
        return records[0]
