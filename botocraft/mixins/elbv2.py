from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet


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
