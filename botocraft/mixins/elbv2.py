from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:

    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
    from botocraft.services.elbv2 import LoadBalancer


# ----------
# Decorators
# ----------


def load_balancer_attributes_to_dict(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., dict[str, Any]]:
    """
    Wraps :py:meth:`botocraft.services.elbv2.LoadBalancerManager.attributes` to
    return a dictionary instead of a list of dictionaries.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> dict[str, Any]:
        attrs = func(self, *args, **kwargs)
        _attrs: dict[str, Any] = {}
        for attr in attrs:
            if attr.Key:  # type: ignore[attr-defined]
                _attrs[attr.Key] = attr.Value  # type: ignore[attr-defined]
        return _attrs

    return wrapper


# ----------
# Mixins
# ----------


class LoadBalancerManagerMixin:
    """
    Mixin for ELBv2 load balancers that adds attributes to the load balancer.
    """

    def get(
        self,
        *,
        LoadBalancerArn: "str | None" = None,  # noqa: N803
        Name: "str | None" = None,  # noqa: N803
    ) -> "LoadBalancer | None":
        """
        Describes the specified load balancers or all of your load balancers.

        Keyword Args:
            LoadBalancerArn: The Amazon Resource Name (ARN) of the load balancer.
            Name: The name of the load balancer.

        Returns:
            A :py:class:`LoadBalancer` object, or :py:data:`None` if no load
            balancer is found.

        """
        from botocraft.services.elbv2 import DescribeLoadBalancersOutput

        if LoadBalancerArn and Name:
            msg = "LoadBalancerArn and Name cannot both be provided"
            raise ValueError(msg)
        if not LoadBalancerArn and not Name:
            msg = "LoadBalancerArn or Name must be provided"
            raise ValueError(msg)
        if LoadBalancerArn:
            args = {"LoadBalancerArns": self.serialize([LoadBalancerArn])}
        else:
            args = {"Names": self.serialize([Name])}
        _response = self.client.describe_load_balancers(
            **{k: v for k, v in args.items() if v is not None}
        )
        response = DescribeLoadBalancersOutput(**_response)

        if response and response.LoadBalancers:
            self.sessionize(response.LoadBalancers[0])
            return response.LoadBalancers[0]
        return None
