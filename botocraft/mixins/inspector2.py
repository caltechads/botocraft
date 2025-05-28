from functools import wraps
from typing import TYPE_CHECKING, Callable, List, Optional

if TYPE_CHECKING:
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
    from botocraft.services.inspector2 import (
        CisScanConfiguration,
        DelegatedAdmin,
        DelegatedAdminAccount,
        Vulnerability,
    )


def convert_delegated_admin(
    func: Callable[..., Optional["DelegatedAdmin"]],
) -> Callable[..., Optional["DelegatedAdminAccount"]]:
    """
    Wraps a boto3 method that returns a list of :py:class:`Reservation` objects
    to return a list of :py:class:`Instance` objects instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional["DelegatedAdminAccount"]:
        from botocraft.services.inspector2 import DelegatedAdminAccount

        self = args[0]
        acct = func(*args, **kwargs)
        if not acct:
            return None
        accts = [
            _acct
            for _acct in DelegatedAdminAccount.objects.using(self.session).list()
            if _acct.accountId == acct.accountId
        ]
        assert len(accts) == 1, "Expected exactly one account"
        _account = DelegatedAdminAccount(
            accountId=acct.accountId,
            status=accts[0].status,
            relationshipStatus=acct.relationshipStatus,
        )
        _account.set_session(self.session)
        return _account

    return wrapper


def list_augment_delegated_admin_accounts(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],  # noqa: F821],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps a boto3 method that returns a list of :py:class:`Reservation` objects
    to return a list of :py:class:`Instance` objects instead.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
        from botocraft.services.inspector2 import DelegatedAdminAccount

        self = args[0]
        qs = func(*args, **kwargs)
        new_accts = []
        for acct in qs.results:
            _acct = DelegatedAdminAccount.objects.using(self.session).get(
                delegatedAdminAccountId=acct.accountId  # type: ignore[attr-defined]
            )
            # DelegatedAdminAccount is a frozen (readonly) model, so we need to
            # do a weird workaround to set the relationshipStatus attribute
            new_accts.append(
                _acct.model_copy(
                    update={"relationshipStatus": _acct.relationshipStatus}
                )
            )
        return PrimaryBoto3ModelQuerySet(new_accts)

    return wrapper


class CisScanConfigurationManagerMixin:
    """
    Mixin class for CIS scan configuration model.
    """

    def get(
        self,
        cisScanConfigurationArn: str | None = None,  # noqa: N803
        scanName: str | None = None,  # noqa: N803
    ) -> Optional["CisScanConfiguration"]:
        """
        Get a CIS scan configuration by ARN.

        Keyword Args:
            cisScanConfigurationArn: The ARN of the CIS scan configuration.
            scanName: The name of the CIS scan configuration.

        Returns:
            The CIS scan configuration.

        """
        from botocraft.services.inspector2 import (
            CisScanConfiguration,
            CisStringFilter,
            ListCisScanConfigurationsFilterCriteria,
        )

        assert any([cisScanConfigurationArn, scanName]), (
            "Either cisScanConfigurationArn or scanName must be provided"
        )

        if cisScanConfigurationArn:
            filter_criteria = ListCisScanConfigurationsFilterCriteria(
                scanConfigurationArnFilters=[
                    CisStringFilter(value=cisScanConfigurationArn, comparison="EQUALS")
                ]
            )
        else:
            filter_criteria = ListCisScanConfigurationsFilterCriteria(
                scanNameFilters=[CisStringFilter(value=scanName, comparison="EQUALS")]
            )

        configs = CisScanConfiguration.objects.using(self.session).list(  # type: ignore[attr-defined]
            filterCriteria=filter_criteria,
        )
        return configs.scanConfigurations[0] if configs.scanConfigurations else None


class VulnerabilityManagerMixin:
    """
    Mixin class for vulnerability model.
    """

    def get(self, vulnerabilityId: str) -> List["Vulnerability"]:  # noqa: N803
        """
        Get a vulnerability by ID or name.

        Keyword Args:
            vulnerabilityId: The ID of the vulnerability.

        Returns:
            The vulnerability.

        """
        from botocraft.services.inspector2 import (
            SearchVulnerabilitiesFilterCriteria,
            Vulnerability,
        )

        response = Vulnerability.objects.using(self.session).get(  # type: ignore[attr-defined]
            filterCriteria=SearchVulnerabilitiesFilterCriteria(
                vulnerabilityIds=[vulnerabilityId]
            )
        )
        return response.vulnerabilities
