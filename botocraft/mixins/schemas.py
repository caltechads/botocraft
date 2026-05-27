from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

from botocraft.mixins.common import ensure_queryset

if TYPE_CHECKING:
    from botocraft.services.abstract import PrimaryBoto3ModelQuerySet
    from botocraft.services.schemas import (
        Discoverer,
        Registry,
        Schema,
    )


def _registry_name_from_call(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """
    Infer registry name from generated manager call arguments.

    Args:
        args: Positional arguments forwarded into generated manager methods.
        kwargs: Keyword arguments forwarded into generated manager methods.

    Raises:
        ValueError: RegistryName is not present in the call arguments.

    Returns:
        Registry name for the current schema-scoped call.

    """
    if "RegistryName" in kwargs and kwargs["RegistryName"] is not None:
        return cast("str", kwargs["RegistryName"])
    if args:
        first_arg = args[0]
        if isinstance(first_arg, str):
            return first_arg
        if hasattr(first_arg, "RegistryName") and first_arg.RegistryName is not None:
            return cast("str", first_arg.RegistryName)
    msg = "RegistryName is required for schema-scoped operations."
    raise ValueError(msg)


def registry_response_to_registry(
    func: Callable[..., Any],
) -> Callable[..., "Registry | None"]:
    """
    Convert registry describe-style responses into public Registry models.

    Args:
        func: Generated manager method that returns a registry response shape.

    Returns:
        Wrapped manager method that returns a public Registry model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "Registry | None":
        from botocraft.services.schemas import Registry

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        registry = Registry(**response.model_dump(exclude_none=True))
        self.sessionize(registry)
        return registry

    return wrapper


def discoverer_response_to_discoverer(
    func: Callable[..., Any],
) -> Callable[..., "Discoverer | None"]:
    """
    Convert discoverer describe-style responses into public Discoverer models.

    Args:
        func: Generated manager method that returns a discoverer response shape.

    Returns:
        Wrapped manager method that returns a public Discoverer model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "Discoverer | None":
        from botocraft.services.schemas import Discoverer

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        discoverer = Discoverer(**response.model_dump(exclude_none=True))
        self.sessionize(discoverer)
        return discoverer

    return wrapper


def schema_response_to_schema(
    func: Callable[..., Any],
) -> Callable[..., "Schema | None"]:
    """
    Convert schema responses into public Schema models with registry context.

    Args:
        func: Generated manager method that returns a schema response shape.

    Returns:
        Wrapped manager method that returns a public Schema model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "Schema | None":
        from botocraft.services.schemas import Schema

        response = func(self, *args, **kwargs)
        if response is None:
            return None
        data = response.model_dump(exclude_none=True)
        data["RegistryName"] = _registry_name_from_call(args, kwargs)
        schema = Schema(**data)
        self.sessionize(schema)
        return schema

    return wrapper


def schema_list_add_registry_name(
    func: Callable[..., "PrimaryBoto3ModelQuerySet"],
) -> Callable[..., "PrimaryBoto3ModelQuerySet"]:
    """
    Reattach registry scope to listed Schema results.

    Args:
        func: Generated manager method that returns listed Schema models.

    Returns:
        Wrapped manager method with RegistryName restored on each result.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> "PrimaryBoto3ModelQuerySet":
        registry_name = _registry_name_from_call(args, kwargs)
        results = ensure_queryset(func(self, *args, **kwargs))
        for schema in results.results:
            cast("Schema", schema).RegistryName = registry_name
        return results

    return wrapper
