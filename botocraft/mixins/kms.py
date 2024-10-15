from typing import TYPE_CHECKING, Callable, List

if TYPE_CHECKING:
    from botocraft.services import KMSKey

# ----------
# Decorators
# ----------


# Service


def kms_keys_only(func: Callable[..., List[str]]) -> Callable[..., List["KMSKey"]]:
    """
    Wraps :py:meth:`botocraft.services.kms.KMSKeyManager.list` to return a list of
    :py:class:`botocraft.services.kms.KMSKey` objects instead of only a list of
    key ids.
    """

    def wrapper(self, *args, **kwargs) -> List["KMSKey"]:
        _ids = func(self, *args, **kwargs)
        return [self.get(KeyId=_id) for _id in _ids]

    return wrapper
