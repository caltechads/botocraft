from functools import wraps
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from botocraft.services.secretsmanager import DescribeSecretResponse, Secret


# ----------
# Decorators
# ----------


def secrets_only(
    func: Callable[..., "DescribeSecretResponse"],
) -> Callable[..., "Secret"]:
    """
    Wrap :py:meth:`botocraft.services.secretsmanager.SecretManager.get` to return a
    :py:class:`botocraft.services.secretsmanager.Secret` object instead of only a
    :py:class:`botocraft.services.secretsmanager.DescribeSecretResponse` object.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "Secret":
        from botocraft.services.secretsmanager import Secret

        response = func(self, *args, **kwargs)
        kwargs = response.model_dump()
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        secret = Secret(**kwargs)
        Secret.objects.sessionize(secret)
        return secret

    return wrapper
