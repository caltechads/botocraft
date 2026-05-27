"""Shared helpers for handwritten service manager mixins."""

from __future__ import annotations

from typing import Any

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet


def arg_value(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    name: str,
    position: int,
) -> Any:
    """
    Return a manager-call argument from keyword or positional form.

    Args:
        args: Positional arguments forwarded into the generated manager method.
        kwargs: Keyword arguments forwarded into the generated manager method.
        name: Keyword argument name to prefer.
        position: Positional argument index after ``self``.

    Returns:
        The matched value, or ``None`` when absent.

    """
    if name in kwargs:
        return kwargs[name]
    if len(args) > position:
        return args[position]
    return None


def coerce_queryset_results(value: Any) -> list[Any]:
    """
    Normalize queryset-like or list-like results into a plain Python list.

    Args:
        value: Result value to normalize.

    Returns:
        A list of underlying result objects.

    """
    if isinstance(value, PrimaryBoto3ModelQuerySet):
        return list(value.results)
    if value is None:
        return []
    return list(value)


def ensure_queryset(value: Any) -> PrimaryBoto3ModelQuerySet:
    """
    Normalize queryset-like or list-like results into a queryset instance.

    Args:
        value: Result value to normalize.

    Returns:
        A queryset wrapping the underlying result objects.

    """
    if isinstance(value, PrimaryBoto3ModelQuerySet):
        return value
    return PrimaryBoto3ModelQuerySet(coerce_queryset_results(value))
