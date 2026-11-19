from typing import TYPE_CHECKING, Any

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.bedrock_agentcore_control import AgentCoreAgentRuntime

#: Create and update arguments whose empty value botocore rejects or that
#: would wipe a setting the caller did not provide. ``allowedPorts`` has
#: minimum length 1. The others default to empty on the model.
_ABSENT_WHEN_EMPTY: frozenset[str] = frozenset(
    {
        "allowedPorts",
        "environmentVariables",
        "filesystemConfigurations",
        "resourceConfigurations",
    }
)


class AgentCoreAgentRuntimeMixin:
    """
    Keep empty AgentCore runtime containers off create and update calls.

    The generated manager dumps the model with ``exclude_none=True`` and
    forwards every remaining value. These fields default to ``[]`` or ``{}``,
    which are not ``None``, so an unused runtime was sent with
    ``allowedPorts=[]`` and botocore rejected it before the request was made.
    """

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Dump the runtime, leaving out containers that are empty.

        Create and update both send this dump. A populated list or dict is
        unchanged.

        Args:
            args: Positional arguments forwarded to the pydantic dump.

        Keyword Args:
            kwargs: Keyword arguments forwarded to the pydantic dump.

        Returns:
            The dumped runtime, without empty ``allowedPorts``,
            ``filesystemConfigurations``, ``resourceConfigurations`` or
            ``environmentVariables``.

        """
        data = super().model_dump(*args, **kwargs)  # type: ignore[misc]
        # ponytail: top-level only. Nested min-length lists are sent only
        # when the caller built the parent object.
        for name in _ABSENT_WHEN_EMPTY:
            if data.get(name) in ([], {}):
                del data[name]
        return data


# -------------
# Manager mixins
# -------------


class AgentCoreAgentRuntimeManagerMixin:
    """
    A mixin class that extends
    :py:class:`~botocraft.services.bedrock_agentcore_control.AgentCoreAgentRuntimeManager`
    to add :py:meth:`list_versions`.

    The generator only returns a
    :py:class:`~botocraft.services.abstract.PrimaryBoto3ModelQuerySet` from
    ``list`` and ``get_many``, so this method is written by hand to give
    runtime versions the same return type as ``list``.
    """

    def list_versions(
        self,
        agentRuntimeId: str,  # noqa: N803
    ) -> "PrimaryBoto3ModelQuerySet[AgentCoreAgentRuntime]":
        """
        List every version of an AgentCore Runtime, following all result pages.

        Each item has the same shape as the runtime returned by ``list``,
        including ``agentRuntimeVersion``, ``status`` and ``lastUpdatedAt``.
        An empty page does not end the listing; the paginator decides when
        there are no more pages.

        Args:
            agentRuntimeId: The unique identifier of the AgentCore Runtime to
                list versions for.

        Returns:
            A queryset of runtime versions, empty if the runtime has none.

        """
        from botocraft.services.bedrock_agentcore_control import AgentCoreAgentRuntime

        paginator = self.client.get_paginator(  # type: ignore[attr-defined]
            "list_agent_runtime_versions"
        )
        results: list[AgentCoreAgentRuntime] = []
        for page in paginator.paginate(
            agentRuntimeId=self.serialize(agentRuntimeId)  # type: ignore[attr-defined]
        ):
            data: dict[str, Any] = {
                key: value for key, value in page.items() if key != "ResponseMetadata"
            }
            results.extend(
                AgentCoreAgentRuntime(**item) for item in data.get("agentRuntimes", [])
            )
        self.sessionize(results)  # type: ignore[attr-defined]
        return PrimaryBoto3ModelQuerySet(results)
