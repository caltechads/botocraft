from typing import TYPE_CHECKING, Any

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.bedrock_agentcore_control import AgentCoreAgentRuntime

#: Create and update members whose empty value botocore rejects (``min``
#: >= 1), plus runtime fields that default to empty and would wipe a setting
#: the caller did not provide. A populated list or map is kept.
#: ``customParameters`` is also a map with no minimum on a registry record;
#: an empty one is omitted too.
# ponytail: one name set for every depth. Per-shape serializers if an empty
# registry ``customParameters`` map must be sent.
_ABSENT_WHEN_EMPTY: frozenset[str] = frozenset(
    {
        "additionalHeaderClaims",
        "additionalPayloadClaims",
        "advertisedScopeMapping",
        "allowedAudience",
        "allowedClients",
        "allowedInstanceTypes",
        "allowedPorts",
        "allowedQueryParameters",
        "allowedRequestHeaders",
        "allowedResponseHeaders",
        "allowedScopes",
        "allowedValues",
        "alternateDomains",
        "anyOf",
        "certificateConfigurations",
        "compositeIdentifier",
        "connections",
        "contentConfigurations",
        "customClaims",
        "customParameters",
        "dimensions",
        "enabled",
        "entryPoint",
        "environmentVariables",
        "errors",
        "examples",
        "exclude",
        "filesystemConfigurations",
        "hostingEnvironments",
        "interceptionPoints",
        "logGroupNamePrefixes",
        "matchValueStringList",
        "metadataSchema",
        "models",
        "multiDimensional",
        "namespaceTemplates",
        "namespaces",
        "operations",
        "requestHeaderAllowlist",
        "requests",
        "resourceConfigurations",
        "securityGroups",
        "serviceNames",
        "statusCodes",
        "strategies",
        "subnets",
        "targetFallback",
        "tokenEndpointAuthMethods",
        "tokens",
        "trafficSplit",
        "triggerConditions",
        "workloadIdentities",
    }
)

#: Empty members that are illegal only under one parent. ``scopes`` has
#: ``min`` 1 on a consent-portal IdP config and is optional on OAuth.
#: ``privateEndpointOverrides`` defaults to ``[]`` on a JWT authorizer.
#: Botocore allows that empty list; create and update still must not send it.
_ABSENT_UNDER_PARENT: frozenset[tuple[str, str]] = frozenset(
    {
        ("customJWTAuthorizer", "privateEndpointOverrides"),
        ("idpConfig", "scopes"),
    }
)


def _omit_empty_containers(data: Any, parent: str | None = None) -> None:
    """
    Drop empty lists and maps that create and update must not send.

    Side Effects:
        Removes those keys from ``data`` and from nested dicts and list items.

    Args:
        data: A ``model_dump`` result, or a nested value inside one.
        parent: The key of the dict that contains ``data``, when ``data`` is
            a dict.

    """
    if isinstance(data, dict):
        for key, value in list(data.items()):
            _omit_empty_containers(value, key)
            if value in ([], {}) and (
                key in _ABSENT_WHEN_EMPTY or (parent, key) in _ABSENT_UNDER_PARENT
            ):
                del data[key]
        return
    if isinstance(data, list):
        for item in data:
            _omit_empty_containers(item)


class OmitEmptyContainersMixin:
    """
    Keep empty AgentCore create and update containers off the wire.

    Generated managers dump the model with ``exclude_none=True`` and forward
    every remaining value. List and map fields default to ``[]`` or ``{}``,
    which are not ``None``. Botocore rejects the ones whose minimum length is
    1 before the request is sent. The in-memory default stays ``[]`` or ``{}``.
    """

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Dump the model, leaving out empty containers at every depth.

        Create and update both send this dump. A populated list or dict is
        unchanged. A read that omitted the field still validates, because the
        default is applied before this dump.

        Args:
            args: Positional arguments forwarded to the pydantic dump.

        Keyword Args:
            kwargs: Keyword arguments forwarded to the pydantic dump.

        Returns:
            The dumped model, without the empty containers named above.

        """
        data = super().model_dump(*args, **kwargs)  # type: ignore[misc]
        _omit_empty_containers(data)
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
