# ----------
# Mixins
# ----------


import json
from typing import TYPE_CHECKING

from botocraft.connectivity import (
    ConnectionResolutionError,
    TunnelAwareConnectionResolver,
)

if TYPE_CHECKING:
    import boto3

    from botocraft.connectivity import ResolvedConnectionTarget
    from botocraft.services.common import Credentials
    from botocraft.services.rds import RDSEndpoint, RDSMasterUserSecret


class RDSInstanceModelMixin:
    """
    A mixin for :py:class:`botocraft.services.rds.RDSInstance` that adds
    some additional methods that we can't auto generate.
    """

    #: RDS instance identifier used in errors and connection labels.
    DBInstanceIdentifier: str
    #: Secret metadata for the master user credentials.
    MasterUserSecret: "RDSMasterUserSecret | None"
    #: Endpoint model containing the instance address and port.
    Endpoint: "RDSEndpoint | None"
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
                f"RDS instance {self.DBInstanceIdentifier} does not have a master "
                "user password in Secrets Manager"
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
        Resolve a direct or tunneled connection target for the DB instance.

        Keyword Args:
            profile: Optional AWS profile override forwarded to the tunnel host
                tunnel helper. Defaults to the active session profile when
                available.

        Raises:
            ConnectionResolutionError: The DB instance does not expose a usable
                endpoint or VPC.

        Returns:
            Context-managed connection target for this DB instance.

        """
        endpoint = getattr(self, "Endpoint", None)
        address = getattr(endpoint, "Address", None)
        port = getattr(endpoint, "Port", None)
        if not address or not port:
            msg = (
                f"RDS instance '{self.DBInstanceIdentifier}' does not have a usable "
                "endpoint."
            )
            raise ConnectionResolutionError(msg)

        vpc = getattr(self, "vpc", None)
        vpc_id = getattr(vpc, "VpcId", None)
        if not vpc_id:
            msg = (
                f"RDS instance '{self.DBInstanceIdentifier}' does not have a "
                "resolvable VPC."
            )
            raise ConnectionResolutionError(msg)

        session = getattr(self, "session", None)
        resolved_profile = profile or getattr(session, "profile_name", None)
        resolver = TunnelAwareConnectionResolver()
        return resolver.open_connection_target(
            host=str(address),
            port=int(port),
            vpc_id=str(vpc_id),
            session=session,
            profile=resolved_profile,
            resource_label=f"RDS instance '{self.DBInstanceIdentifier}'",
        )
