"""
Handwritten helpers for the generated SSM ``Parameter`` manager.

AWS's ``GetParameters``/``DescribeParameters`` operations never return
resource tags, and ``PutParameter``'s own ``Tags`` argument only takes
effect when the call creates a parameter -- AWS's own API reference:
"To add tags to an existing Systems Manager parameter, use the
AddTagsToResource operation." These decorators hydrate ``Parameter.Tags``
on read via a follow-up ``list_tags_for_resource`` call, and write it on
write via a follow-up ``add_tags_to_resource`` call, so ``Parameter.Tags``
behaves like every other Botocraft primary model's tag field despite SSM's
API not supporting it directly on the main calls.

.. note::
    Breaking change: ``ParameterManager.create()`` no longer accepts an
    explicit ``Tags=`` keyword argument. Because ``Tags`` is now a real
    field on the ``Parameter`` model, ``create()`` reads it from
    ``model.model_dump()`` instead. Set tags via
    ``Parameter(..., Tags=[...])`` at construction time, the same way you
    would set any other field, then pass that model to ``create()``.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from botocraft.services.ssm import Parameter

# ----------
# Decorators
# ----------


def single_parameter_include_tags(
    func: Callable[..., Parameter | None],
) -> Callable[..., Parameter | None]:
    """
    Decorator to hydrate a :py:class:`botocraft.services.ssm.Parameter`
    object's ``Tags`` field via a follow-up ``list_tags_for_resource`` call.

    Unlike the DocDB tag-hydration decorators this mirrors, this one must
    handle a ``None`` result: ``ParameterManager.get`` returns ``None``
    when the parameter doesn't exist, and there is nothing to hydrate.

    Args:
        func: The ``ParameterManager.get`` method to wrap.

    Returns:
        A wrapped version of ``func`` that hydrates ``Tags`` on its result.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Parameter | None:
        response = func(self, *args, **kwargs)
        if response is None:
            return None
        tags = self.client.list_tags_for_resource(
            ResourceType="Parameter", ResourceId=response.Name
        )
        response.Tags = tags["TagList"]
        return response

    return wrapper


def parameter_update_writes_tags(
    func: Callable[..., int],
) -> Callable[..., int]:
    """
    Decorator to write ``Tags`` via ``add_tags_to_resource`` after
    ``ParameterManager.update``'s normal ``put_parameter`` call.

    AWS ignores ``PutParameter``'s own ``Tags`` argument on an overwrite of
    an already-existing parameter (see module docstring), so it never
    reaches the generated call at all here: this wrapper reads
    ``Tags`` off the model (or an explicit ``Tags=`` kwarg, which wins if
    given) and applies it as a separate call, after the value write
    succeeds.

    Args:
        func: The ``ParameterManager.update`` method to wrap.

    Returns:
        A wrapped version of ``func`` that also writes ``Tags`` via
        ``add_tags_to_resource``.

    """

    @wraps(func)
    def wrapper(self, model, *args, **kwargs) -> int:
        explicit_tags = kwargs.pop("Tags", None)
        version = func(self, model, *args, **kwargs)
        tags = (
            explicit_tags
            if explicit_tags is not None
            else getattr(model, "Tags", None)
        )
        if tags:
            self.client.add_tags_to_resource(
                ResourceType="Parameter",
                ResourceId=model.Name,
                Tags=[
                    {"Key": tag.Key, "Value": tag.Value}
                    if hasattr(tag, "Key")
                    else tag
                    for tag in tags
                ],
            )
        return version

    return wrapper
