# mypy: disable-error-code="attr-defined"
from functools import wraps
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

# ----------
# Decorators
# ----------


# Service


def kms_keys_only(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Wraps :py:meth:`botocraft.services.kms.KMSKeyManager.list` to return a list of
    :py:class:`botocraft.services.kms.KMSKey` objects instead of only a list of
    key ids.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

        _ids = func(self, *args, **kwargs)
        return PrimaryBoto3ModelQuerySet([self.get(KeyId=_id.KeyId) for _id in _ids])

    return wrapper
