from typing import TYPE_CHECKING, Any

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.bedrock_agentcore_control import AgentCoreAgentRuntime

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
