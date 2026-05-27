"""Handwritten helpers for generated CodeConnections service managers."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, cast

from botocraft.mixins.common import arg_value, coerce_queryset_results
from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from botocraft.services.codeconnections import (
        Connection,
        Host,
        SyncBlocker,
        SyncBlockerSummary,
        SyncConfiguration,
    )
    from botocraft.services.common import Tag


class CodeConnectionsResponseHelper:
    """
    Hydrate CodeConnections manager responses into stable public models.

    Args:
        manager: Generated manager instance that owns boto3 client and session.

    """

    #: Generated manager instance used for follow-up AWS calls and sessionization.
    manager: Any

    def __init__(self, manager: Any) -> None:
        """
        Initialize helper for one generated manager call.

        Args:
            manager: Generated manager instance that owns boto3 client and session.

        """
        #: Generated manager instance used for follow-up AWS calls and sessionization.
        self.manager = manager

    def _tag_models(self, tags: list[dict[str, Any]] | None) -> list[Tag]:
        """
        Convert raw tag dictionaries into generated tag models.

        Args:
            tags: Raw tag dictionaries returned by boto3.

        Returns:
            Generated tag models.

        """
        from botocraft.services.common import Tag

        if not tags:
            return []
        return [Tag(**tag) for tag in tags]

    def _load_tags(self, arn: str | None) -> list[Tag]:
        """
        Load tag models for one resource ARN.

        Args:
            arn: Resource ARN to query.

        Returns:
            Tag models for resource, or empty list when ARN absent.

        """
        if not arn:
            return []
        response = self.manager.client.list_tags_for_resource(ResourceArn=arn)
        return self._tag_models(response.get("Tags"))

    def _sessionize(self, model: Any) -> Any:
        """
        Attach active boto3 session to one model or queryset.

        Args:
            model: Model or queryset to sessionize.

        Returns:
            Same object after sessionization.

        Side Effects:
            Binds manager session to returned object graph.

        """
        self.manager.sessionize(model)
        return model

    def _model_payload(
        self,
        response: Any,
        nested_key: str | None = None,
    ) -> dict[str, Any]:
        """
        Convert generated response wrapper into constructor payload.

        Args:
            response: Generated response wrapper or model.
            nested_key: Optional nested member to unwrap first.

        Returns:
            Constructor payload dictionary.

        """
        if response is None:
            return {}
        if hasattr(response, "model_dump"):
            payload = response.model_dump(exclude_none=True)
        elif isinstance(response, dict):
            payload = dict(response)
        else:
            payload = dict(vars(response))
        if nested_key is not None:
            nested = payload.get(nested_key)
            if isinstance(nested, dict):
                return nested
            return {}
        return payload

    def connection_from_get(
        self,
        response: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Connection | None:
        """
        Convert get-connection response into public connection model.

        Args:
            response: Generated response object from ``get_connection``.
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Public connection model, or ``None`` when response absent.

        """
        from botocraft.services.codeconnections import Connection

        if response is None:
            return None
        payload = self._model_payload(response, "ConnectionInstance")
        if payload.get("ConnectionArn") is None:
            arn = arg_value(args, kwargs, "arn", 0)
            if arn is not None:
                payload["ConnectionArn"] = arn
        connection = Connection(**payload)
        connection.Tags = self._load_tags(connection.ConnectionArn)
        return cast("Connection", self._sessionize(connection))

    def connection_from_create(self, response: Any) -> Connection | None:
        """
        Convert create-connection response into hydrated public model.

        Args:
            response: Generated response object from ``create_connection``.

        Returns:
            Hydrated public connection model, or ``None`` when response absent.

        """
        if response is None:
            return None
        payload = self._model_payload(response)
        arn = cast("str | None", payload.get("ConnectionArn"))
        connection = self.manager.get(arn=arn) if arn else None
        if connection is None:
            return None
        if not getattr(connection, "Tags", None):
            connection.Tags = self._tag_models(
                cast("list[dict[str, Any]] | None", payload.get("Tags"))
            )
        if not getattr(connection, "Tags", None):
            connection.Tags = self._load_tags(connection.ConnectionArn)
        return cast("Connection", self._sessionize(connection))

    def connections_with_tags(self, results: Any) -> PrimaryBoto3ModelQuerySet:
        """
        Attach tags to listed connection models.

        Args:
            results: List or queryset of connection models.

        Returns:
            Queryset of enriched connection models.

        """
        connections = []
        for connection in coerce_queryset_results(results):
            connection.Tags = self._load_tags(connection.ConnectionArn)
            connections.append(connection)
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", connections))
        return cast("PrimaryBoto3ModelQuerySet", self._sessionize(query_set))

    def host_from_get(
        self,
        response: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Host | None:
        """
        Convert get-host response into public host model.

        Args:
            response: Generated response object from ``get_host``.
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Public host model, or ``None`` when response absent.

        """
        from botocraft.services.codeconnections import Host

        if response is None:
            return None
        payload = self._model_payload(response)
        if payload.get("HostArn") is None:
            arn = arg_value(args, kwargs, "arn", 0)
            if arn is not None:
                payload["HostArn"] = arn
        host = Host(**payload)
        host.Tags = self._load_tags(host.HostArn)
        return cast("Host", self._sessionize(host))

    def host_from_create(self, response: Any) -> Host | None:
        """
        Convert create-host response into hydrated public model.

        Args:
            response: Generated response object from ``create_host``.

        Returns:
            Hydrated public host model, or ``None`` when response absent.

        """
        if response is None:
            return None
        payload = self._model_payload(response)
        arn = cast("str | None", payload.get("HostArn"))
        host = self.manager.get(arn=arn) if arn else None
        if host is None:
            return None
        if not getattr(host, "Tags", None):
            host.Tags = self._tag_models(
                cast("list[dict[str, Any]] | None", payload.get("Tags"))
            )
        if not getattr(host, "Tags", None):
            host.Tags = self._load_tags(host.HostArn)
        return cast("Host", self._sessionize(host))

    def host_from_update(self, *args: Any, **kwargs: Any) -> Host | None:
        """
        Re-fetch host after empty update response.

        Args:
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Hydrated public host model, or ``None`` when ARN absent.

        """
        maybe_arn = arg_value(args, kwargs, "arn", 0)
        arn = cast("str | None", maybe_arn if isinstance(maybe_arn, str) else None)
        if arn is None and args:
            model = args[0]
            arn = cast("str | None", getattr(model, "HostArn", None))
        if arn is None and "model" in kwargs:
            arn = cast("str | None", getattr(kwargs["model"], "HostArn", None))
        host = self.manager.get(arn=arn) if arn else None
        if host is None:
            return None
        host.Tags = self._load_tags(host.HostArn)
        return cast("Host", self._sessionize(host))

    def hosts_with_tags(self, results: Any) -> PrimaryBoto3ModelQuerySet:
        """
        Attach tags to listed host models.

        Args:
            results: List or queryset of host models.

        Returns:
            Queryset of enriched host models.

        """
        hosts = []
        for host in coerce_queryset_results(results):
            host.Tags = self._load_tags(host.HostArn)
            hosts.append(host)
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", hosts))
        return cast("PrimaryBoto3ModelQuerySet", self._sessionize(query_set))

    def sync_configuration_from_response(
        self,
        response: Any,
    ) -> SyncConfiguration | None:
        """
        Convert wrapped sync-configuration response into public model.

        Args:
            response: Generated response object from sync-configuration methods.

        Returns:
            Public sync-configuration model, or ``None`` when response absent.

        """
        from botocraft.services.codeconnections import SyncConfiguration

        if response is None:
            return None
        payload = self._model_payload(response)
        sync_payload = cast(
            "dict[str, Any]",
            payload.get("SyncConfigurationInstance", payload),
        )
        sync_configuration = SyncConfiguration(**sync_payload)
        return cast("SyncConfiguration", self._sessionize(sync_configuration))

    def repository_sync_definitions_with_context(
        self,
        results: Any,
        *args: Any,
        **kwargs: Any,
    ) -> PrimaryBoto3ModelQuerySet:
        """
        Reattach scope fields to listed repository sync definitions.

        Args:
            results: List or queryset of repository sync definitions.
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Queryset of repository sync definitions with scope fields restored.

        """
        from botocraft.services.codeconnections import RepositorySyncDefinition

        repository_link_id = cast(
            "str | None",
            arg_value(args, kwargs, "RepositoryLinkId", 0),
        )
        sync_type = cast("str | None", arg_value(args, kwargs, "SyncType", 1))
        definitions = []
        for definition in coerce_queryset_results(results):
            payload = definition.model_dump(exclude_none=True)
            payload["RepositoryLinkId"] = repository_link_id
            payload["SyncType"] = sync_type
            definitions.append(RepositorySyncDefinition(**payload))
        query_set = PrimaryBoto3ModelQuerySet(cast("list[Boto3Model]", definitions))
        return cast("PrimaryBoto3ModelQuerySet", self._sessionize(query_set))

    def sync_blocker_summary_from_response(
        self,
        response: Any,
        *args: Any,
        **kwargs: Any,
    ) -> SyncBlockerSummary | None:
        """
        Convert wrapped sync-blocker-summary response into public model.

        Args:
            response: Generated response object from ``get_sync_blocker_summary``.
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Public sync-blocker-summary model, or ``None`` when response absent.

        """
        from botocraft.services.codeconnections import SyncBlockerSummary

        if response is None:
            return None
        payload = self._model_payload(response, "SyncBlockerSummaryInstance")
        sync_type = cast("str | None", arg_value(args, kwargs, "SyncType", 0))
        if sync_type is not None:
            payload["SyncType"] = sync_type
        summary = SyncBlockerSummary(**payload)
        for blocker in summary.LatestBlockers or []:
            blocker.ResourceName = summary.ResourceName
            blocker.ParentResourceName = summary.ParentResourceName
            blocker.SyncType = sync_type
        return cast("SyncBlockerSummary", self._sessionize(summary))

    def sync_blocker_from_update(
        self,
        response: Any,
        *args: Any,
        **kwargs: Any,
    ) -> SyncBlocker | None:
        """
        Convert update-sync-blocker response into public blocker model.

        Args:
            response: Generated response object from ``update_sync_blocker``.
            *args: Positional arguments from wrapped manager call.

        Keyword Args:
            **kwargs: Keyword arguments from wrapped manager call.

        Returns:
            Public sync-blocker model, or ``None`` when response absent.

        """
        from botocraft.services.codeconnections import SyncBlocker

        if response is None:
            return None
        payload = self._model_payload(response)
        blocker_payload = cast(
            "dict[str, Any]",
            payload.get("SyncBlockerInstance", {}),
        )
        model = args[0] if args else kwargs.get("model")
        blocker_payload["ResourceName"] = payload.get(
            "ResourceName",
            getattr(model, "ResourceName", None)
            or arg_value(args, kwargs, "ResourceName", 2),
        )
        blocker_payload["ParentResourceName"] = payload.get("ParentResourceName")
        blocker_payload["SyncType"] = getattr(model, "SyncType", None) or arg_value(
            args,
            kwargs,
            "SyncType",
            1,
        )
        blocker = SyncBlocker(**blocker_payload)
        return cast("SyncBlocker", self._sessionize(blocker))


def connection_create_to_connection(
    func: Callable[..., Any],
) -> Callable[..., Connection | None]:
    """
    Hydrate create-connection responses into public connection models.

    Args:
        func: Generated manager method returning create-connection wrapper.

    Returns:
        Wrapped manager method returning public connection model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Connection | None:
        response = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).connection_from_create(response)

    return wrapper


def connection_response_to_connection(
    func: Callable[..., Any],
) -> Callable[..., Connection | None]:
    """
    Flatten get-connection responses into public connection models.

    Args:
        func: Generated manager method returning get-connection wrapper.

    Returns:
        Wrapped manager method returning public connection model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Connection | None:
        response = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).connection_from_get(
            response,
            *args,
            **kwargs,
        )

    return wrapper


def connections_include_tags(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Enrich listed connections with tags.

    Args:
        func: Generated manager method returning connection list.

    Returns:
        Wrapped manager method returning enriched queryset.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        results = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).connections_with_tags(results)

    return wrapper


def host_create_to_host(
    func: Callable[..., Any],
) -> Callable[..., Host | None]:
    """
    Hydrate create-host responses into public host models.

    Args:
        func: Generated manager method returning create-host wrapper.

    Returns:
        Wrapped manager method returning public host model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Host | None:
        response = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).host_from_create(response)

    return wrapper


def host_response_to_host(
    func: Callable[..., Any],
) -> Callable[..., Host | None]:
    """
    Flatten get-host responses into public host models.

    Args:
        func: Generated manager method returning get-host wrapper.

    Returns:
        Wrapped manager method returning public host model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Host | None:
        response = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).host_from_get(
            response,
            *args,
            **kwargs,
        )

    return wrapper


def hosts_include_tags(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Enrich listed hosts with tags.

    Args:
        func: Generated manager method returning host list.

    Returns:
        Wrapped manager method returning enriched queryset.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        results = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).hosts_with_tags(results)

    return wrapper


def host_update_to_host(
    func: Callable[..., Any],
) -> Callable[..., Host | None]:
    """
    Re-fetch host after empty update response.

    Args:
        func: Generated manager method returning no update payload.

    Returns:
        Wrapped manager method returning public host model.

    Side Effects:
        Performs follow-up ``get_host`` and ``list_tags_for_resource`` calls.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Host | None:
        func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).host_from_update(
            *args,
            **kwargs,
        )

    return wrapper


def sync_configuration_response_to_sync_configuration(
    func: Callable[..., Any],
) -> Callable[..., SyncConfiguration | None]:
    """
    Flatten wrapped sync-configuration responses into public models.

    Args:
        func: Generated manager method returning sync-configuration wrapper.

    Returns:
        Wrapped manager method returning public sync-configuration model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> SyncConfiguration | None:
        response = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).sync_configuration_from_response(
            response
        )

    return wrapper


def repository_sync_definitions_add_context(
    func: Callable[..., Any],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Reattach scope fields to listed repository sync definitions.

    Args:
        func: Generated manager method returning repository sync definitions.

    Returns:
        Wrapped manager method returning scoped queryset.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> PrimaryBoto3ModelQuerySet:
        results = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(
            self
        ).repository_sync_definitions_with_context(results, *args, **kwargs)

    return wrapper


def sync_blocker_summary_response_to_sync_blocker_summary(
    func: Callable[..., Any],
) -> Callable[..., SyncBlockerSummary | None]:
    """
    Flatten wrapped sync-blocker-summary responses into public models.

    Args:
        func: Generated manager method returning sync-blocker-summary wrapper.

    Returns:
        Wrapped manager method returning public sync-blocker-summary model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> SyncBlockerSummary | None:
        response = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).sync_blocker_summary_from_response(
            response,
            *args,
            **kwargs,
        )

    return wrapper


def update_sync_blocker_response_to_sync_blocker(
    func: Callable[..., Any],
) -> Callable[..., SyncBlocker | None]:
    """
    Flatten wrapped update-sync-blocker responses into public blocker models.

    Args:
        func: Generated manager method returning update-sync-blocker wrapper.

    Returns:
        Wrapped manager method returning public sync-blocker model.

    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> SyncBlocker | None:
        if not args and "model" not in kwargs and "Id" in kwargs:

            class _UpdateSyncBlockerRequest:
                """
                Minimal request shim for generated sync-blocker update method.

                Args:
                    payload: Serialized request payload for ``update_sync_blocker``.

                """

                #: Serialized request payload for generated manager call.
                payload: dict[str, Any]

                def __init__(self, payload: dict[str, Any]) -> None:
                    """
                    Initialize request shim.

                    Args:
                        payload: Serialized request payload for ``update_sync_blocker``.

                    """
                    self.payload = payload

                def model_dump(
                    self,
                    *,
                    exclude_none: bool = True,
                    by_alias: bool = True,
                ) -> dict[str, Any]:
                    """
                    Return generated-model compatible payload.

                    Keyword Args:
                        exclude_none: Unused compatibility flag.
                        by_alias: Unused compatibility flag.

                    Returns:
                        Serialized request payload.

                    """
                    del exclude_none, by_alias
                    return dict(self.payload)

            model = _UpdateSyncBlockerRequest(
                {
                    "Id": kwargs["Id"],
                    "SyncType": kwargs["SyncType"],
                    "ResourceName": kwargs["ResourceName"],
                    "ResolvedReason": kwargs["ResolvedReason"],
                }
            )
            response = func(self, model)
        else:
            response = func(self, *args, **kwargs)
        return CodeConnectionsResponseHelper(self).sync_blocker_from_update(
            response,
            *args,
            **kwargs,
        )

    return wrapper
