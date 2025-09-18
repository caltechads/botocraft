from functools import wraps
from typing import TYPE_CHECKING, Callable, cast

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.iam import AttachedPolicy, IAMPolicy

# ------------------------------------------------------------
# Decorators
# ------------------------------------------------------------


def role_inline_policies_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.iam.IAMRoleManager.list_policies` to
    return a :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.iam.GetRolePolicyResponse` objects instead of
    only a list of names.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        # We need to import IAMUser here because otherwise we get a circular import
        from botocraft.services.iam import IAMGroup

        groupname = args[0]
        names = func(self, *args, **kwargs)
        policies = [
            IAMGroup.objects.get_policy(GroupName=groupname, PolicyName=name)
            for name in names
        ]
        return PrimaryBoto3ModelQuerySet(policies)

    return wrapper


def role_attached_policies_only(
    func: Callable[..., list["AttachedPolicy"]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.iam.IAMRoleManager.list_attached_policies` to
    return a :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.iam.IAMPolicy` objects instead of only a list
    of names.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        # We need to import IAMRole here because otherwise we get a circular import
        from botocraft.services.iam import IAMPolicy

        attached_policies = func(self, *args, **kwargs)
        policies = [
            IAMPolicy.objects.get(policy.PolicyArn) for policy in attached_policies
        ]
        return PrimaryBoto3ModelQuerySet(policies)

    return wrapper


def group_inline_policies_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.iam.IAMGroupManager.list_policies` to
    return a :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.iam.GetGroupPolicyResponse` objects instead of
    only a list of names.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        # We need to import IAMUser here because otherwise we get a circular import
        from botocraft.services.iam import IAMGroup

        groupname = args[0]
        names = func(self, *args, **kwargs)
        policies = [
            IAMGroup.objects.get_policy(GroupName=groupname, PolicyName=name)
            for name in names
        ]
        return PrimaryBoto3ModelQuerySet(policies)

    return wrapper


def group_attached_policies_only(
    func: Callable[..., list["AttachedPolicy"]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.iam.IAMGroupManager.list_attached_policies` to
    return a :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.iam.IAMPolicy` objects instead of only a list
    of names.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        # We need to import IAMGroup here because otherwise we get a circular import
        from botocraft.services.iam import IAMPolicy

        attached_policies = func(self, *args, **kwargs)
        policies = [
            IAMPolicy.objects.get(policy.PolicyArn) for policy in attached_policies
        ]
        return PrimaryBoto3ModelQuerySet(policies)

    return wrapper


def user_inline_policies_only(
    func: Callable[..., list[str]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.iam.IAMPolicyManager.list_policies` to
    return a :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.iam.GetUserPolicyResponse` objects instead of
    only a list of names.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        # We need to import IAMUser here because otherwise we get a circular import
        from botocraft.services.iam import IAMUser

        username = args[0]
        names = func(self, *args, **kwargs)
        policies = [
            IAMUser.objects.get_policy(UserName=username, PolicyName=name)
            for name in names
        ]
        return PrimaryBoto3ModelQuerySet(policies)

    return wrapper


def iam_attached_policies_only(
    func: Callable[..., list["AttachedPolicy"]],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps
    :py:meth:`botocraft.services.iam.IAMPolicyManager.list_attached_policies`
    and any other method that returns a list of IAMPolicy (as opposed to inline
    policy) names to return a :py:class:`PrimaryBoto3ModelQuerySet` of
    :py:class:`botocraft.services.iam.IAMPolicy` objects instead of only a list
    of names.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        # We need to import IAMPolicy here because otherwise we get a circular import
        from botocraft.services.iam import IAMPolicy

        attached_policies = func(self, *args, **kwargs)
        policies = [
            IAMPolicy.objects.get(policy.PolicyArn) for policy in attached_policies
        ]
        return PrimaryBoto3ModelQuerySet(policies)

    return wrapper


# ------------------------------------------------------------
# Model Mixins
# ------------------------------------------------------------


class IAMPolicyMixin:
    """
    A mixin that adds a ``policy`` property to a model instance.  This
    is intended to be used with :py:class:`Boto3Model` classes that have
    a ``Policy`` attribute.
    """

    @property
    def is_in_use(self) -> bool:
        """
        Return True if the policy is used by any users, roles, or groups.
        """
        entities = self.entities()  # type: ignore[attr-defined]
        return all(
            [
                len(entities.PolicyUsers) > 0,
                len(entities.PolicyRoles) > 0,
                len(entities.PolicyGroups) > 0,
            ]
        )


# ------------------------------------------------------------
# Manager Mixins
# ------------------------------------------------------------


class IAMPolicyManagerMixin:
    """
    A mixin that adds a ``policy`` property to a manager instance.  This
    is intended to be used with :py:class:`Boto3ModelManager` classes that have
    a ``Policy`` attribute.
    """

    def not_in_use(
        self,
        policies: list["IAMPolicy"] | None = None,
    ) -> list["IAMPolicy"]:
        """
        Return a list of policies that are not currently in use.

        If ``policies`` is not specified, all policies will be filtered.

        Keyword Args:
            policies: A list of policies to filter.

        """
        if policies is None:
            policies = self.list().all()  # type: ignore[attr-defined]
        cast("list[IAMPolicy]", policies)
        return [policy for policy in policies if not policy.is_in_use]  # type: ignore[attr-defined, union-attr]

    def in_use(
        self,
        policies: list["IAMPolicy"] | None = None,
    ) -> list["IAMPolicy"]:
        """
        Return a list of policies that are in use.

        Keyword Args:
            policies: A list of policies to filter.

        """
        if policies is None:
            policies = self.list().all()  # type: ignore[attr-defined]
        cast("list[IAMPolicy]", policies)
        return [policy for policy in policies if policy.is_in_use]  # type: ignore[attr-defined, union-attr]
