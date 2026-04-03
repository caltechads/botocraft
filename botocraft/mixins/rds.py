# ----------
# Mixins
# ----------


import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from botocraft.services.common import Credentials


class RDSInstanceModelMixin:
    """
    A mixin for :py:class:`botocraft.services.rds.RDSInstance` that adds
    some additional methods that we can't auto generate.
    """

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
