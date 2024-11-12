from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, List

if TYPE_CHECKING:
    from botocraft.services import LoadBalancerAttribute


# ----------
# Decorators
# ----------


def load_balancer_attributes_to_dict(
    func: Callable[..., List["LoadBalancerAttribute"]],
) -> Callable[..., Dict[str, Any]]:
    """
    Wraps :py:meth:`botocraft.services.elbv2.LoadBalancerManager.attributes` to
    return a dictionary instead of a list of dictionaries.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Dict[str, Any]:
        attrs = func(self, *args, **kwargs)
        _attrs: Dict[str, Any] = {}
        for attr in attrs:
            if attr.Key:
                _attrs[attr.Key] = attr.Value
        return _attrs

    return wrapper
