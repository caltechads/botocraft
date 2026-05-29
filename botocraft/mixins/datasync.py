"""Handwritten helpers for generated DataSync service managers."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, cast

from botocore.exceptions import ClientError

from botocraft.services.abstract import Boto3Model, PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from collections.abc import Callable

    from botocraft.services.common import Tag
    from botocraft.services.datasync import DataSyncTaskExecution


def _deserialize_tags(raw_tags: list[dict[str, Any]] | list[Tag] | None) -> list[Tag]:
    """
    Normalize raw DataSync tag payloads into Botocraft ``Tag`` models.

    Args:
        raw_tags: Raw tags returned by boto3 or already-built tag models.

    Returns:
        Normalized ``Tag`` models.

    """
    from botocraft.services.common import Tag

    if not raw_tags:
        return []
    tags: list[Tag] = []
    for raw_tag in raw_tags:
        if isinstance(raw_tag, Tag):
            tags.append(raw_tag)
        else:
            tags.append(Tag(**raw_tag))
    return tags


def _extract_resource_arn(resource: Any) -> str | None:
    """
    Return best-effort primary ARN from generated DataSync model or response.

    Args:
        resource: Generated model or response wrapper.

    Returns:
        ARN-like identifier when present, otherwise ``None``.

    """
    for attribute in ("pk", "AgentArn", "TaskArn", "TaskExecutionArn", "LocationArn"):
        value = getattr(resource, attribute, None)
        if value is not None:
            return cast("str", value)
    return None


def _list_resource_tags(manager: Any, resource_arn: str) -> list[Tag]:
    """
    Return tags for one DataSync resource.

    Args:
        manager: Generated DataSync manager instance.
        resource_arn: ARN of resource whose tags should be loaded.

    Returns:
        Current tags attached to resource.

    """
    response = manager.client.list_tags_for_resource(  # type: ignore[attr-defined]
        ResourceArn=resource_arn
    )
    return _deserialize_tags(response.get("Tags"))


def _hydrate_tags(manager: Any, resource: Any) -> None:
    """
    Populate ``Tags`` on one DataSync model when field exists.

    Args:
        manager: Generated DataSync manager instance.
        resource: Model instance to enrich.

    Side Effects:
        Updates ``resource.Tags`` in place when supported.

    """
    if resource is None or not hasattr(resource, "Tags"):
        return
    resource_arn = _extract_resource_arn(resource)
    if resource_arn is None:
        return
    resource.Tags = _list_resource_tags(manager, resource_arn)


def _sync_tags(manager: Any, resource_arn: str, tags: list[Tag]) -> None:
    """
    Reconcile remote DataSync tags with desired in-memory state.

    Args:
        manager: Generated DataSync manager instance.
        resource_arn: ARN of resource whose tags should be updated.
        tags: Desired final tag set for resource.

    Side Effects:
        Calls DataSync tag and untag APIs to match provided tag set.

    """
    current_tags = _list_resource_tags(manager, resource_arn)
    current = {tag.Key: tag.Value for tag in current_tags}
    desired = {tag.Key: tag.Value for tag in tags}

    keys_to_remove = sorted(set(current) - set(desired))
    tags_to_upsert = [tag for tag in tags if current.get(tag.Key) != tag.Value]

    if keys_to_remove:
        manager.client.untag_resource(  # type: ignore[attr-defined]
            ResourceArn=resource_arn,
            Keys=keys_to_remove,
        )
    if tags_to_upsert:
        manager.client.tag_resource(  # type: ignore[attr-defined]
            ResourceArn=resource_arn,
            Tags=manager.serialize(tags_to_upsert),  # type: ignore[attr-defined]
        )


def datasync_add_tags(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Attach tags to one DataSync resource returned by a manager call.

    Args:
        func: Manager method that returns one model instance.

    Returns:
        Wrapped manager method that hydrates tags.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        resource = func(self, *args, **kwargs)
        _hydrate_tags(self, resource)
        return resource

    return wrapper


def datasync_add_tags_to_queryset(
    func: Callable[..., PrimaryBoto3ModelQuerySet],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Attach tags to all DataSync resources returned by a manager call.

    Args:
        func: Manager method that returns model queryset.

    Returns:
        Wrapped manager method that hydrates tags on each model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> PrimaryBoto3ModelQuerySet:
        resources = func(self, *args, **kwargs)
        for resource in resources:
            _hydrate_tags(self, resource)
        return resources

    return wrapper


def datasync_refresh_after_create(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Re-fetch full DataSync resource after create-style manager calls.

    Args:
        func: Generated manager method that returns partial model with primary key.

    Returns:
        Wrapped method that returns hydrated full model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        created = func(self, *args, **kwargs)
        if created is None:
            return None
        resource_arn = _extract_resource_arn(created)
        if resource_arn is None:
            return created
        return self.get(resource_arn)

    return wrapper


def datasync_refresh_after_update(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Re-fetch full DataSync resource after update-style manager calls.

    Args:
        func: Generated manager method that mutates existing model.

    Returns:
        Wrapped method that returns refreshed full model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        model = cast("Any", args[0] if args else kwargs.get("model"))
        resource_arn = _extract_resource_arn(model)
        desired_tags = cast("list[Tag] | None", getattr(model, "Tags", None))
        func(self, *args, **kwargs)
        if resource_arn is None:
            return None
        if desired_tags is not None:
            _sync_tags(self, resource_arn, desired_tags)
        return self.get(resource_arn)

    return wrapper


def datasync_task_execution_from_start(
    func: Callable[..., DataSyncTaskExecution | None],
) -> Callable[..., DataSyncTaskExecution | None]:
    """
    Convert ``start_task_execution`` response into full task-execution model.

    Args:
        func: Generated task-manager method that returns task-execution stub.

    Returns:
        Wrapped method that loads the full task execution model.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> DataSyncTaskExecution | None:
        execution = func(self, *args, **kwargs)
        if execution is None:
            return None
        execution_arn = cast("str | None", getattr(execution, "TaskExecutionArn", None))
        if execution_arn is None:
            return execution
        from botocraft.services.datasync import DataSyncTaskExecutionManager

        manager = DataSyncTaskExecutionManager()
        manager.session = self.session
        return manager.get(execution_arn)

    return wrapper


def _typed_location_list(
    manager: Any,
    *,
    location_type_filters: list[str] | None,
) -> PrimaryBoto3ModelQuerySet:
    """
    List hydrated locations for one DataSync location subtype.

    Args:
        manager: Generated DataSync location manager.

    Keyword Args:
        location_type_filters: Optional ``LocationType`` values to pre-filter by.

    Returns:
        Queryset of fully described location models for this subtype.

    """
    paginator = manager.client.get_paginator("list_locations")  # type: ignore[attr-defined]
    paginate_kwargs: dict[str, Any] = {}
    if location_type_filters:
        paginate_kwargs["Filters"] = [
            {
                "Name": "LocationType",
                "Operator": "In" if len(location_type_filters) > 1 else "Equals",
                "Values": location_type_filters,
            }
        ]
    results: list[Boto3Model] = []
    for page in paginator.paginate(**paginate_kwargs):
        for location in page.get("Locations", []):
            try:
                loaded = manager.get(location["LocationArn"])
            except ClientError:
                continue
            if loaded is not None:
                results.append(cast("Boto3Model", loaded))
    return PrimaryBoto3ModelQuerySet(results)


def _location_list_decorator(
    *,
    location_type_filters: list[str] | None,
) -> Callable[
    [Callable[..., PrimaryBoto3ModelQuerySet]],
    Callable[..., PrimaryBoto3ModelQuerySet],
]:
    """
    Build decorator for subtype-aware DataSync location listing.

    Keyword Args:
        location_type_filters: Optional ``LocationType`` values to pre-filter by.

    Returns:
        Decorator that replaces lightweight list results with hydrated models.

    """

    def decorator(
        func: Callable[..., PrimaryBoto3ModelQuerySet],
    ) -> Callable[..., PrimaryBoto3ModelQuerySet]:
        @wraps(func)
        def wrapper(self, *_args, **_kwargs) -> PrimaryBoto3ModelQuerySet:
            return _typed_location_list(
                self,
                location_type_filters=location_type_filters,
            )

        return wrapper

    return decorator

#: Decorator that lists Azure Blob locations by scanning all DataSync locations.
datasync_list_azure_blob_locations = _location_list_decorator(
    location_type_filters=None
)
#: Decorator that lists EFS-backed DataSync locations.
datasync_list_efs_locations = _location_list_decorator(location_type_filters=["EFS"])
#: Decorator that lists FSx for Lustre DataSync locations.
datasync_list_fsx_lustre_locations = _location_list_decorator(
    location_type_filters=["FSX_LUSTRE"]
)
#: Decorator that lists FSx for ONTAP DataSync locations.
datasync_list_fsx_ontap_locations = _location_list_decorator(
    location_type_filters=["FSX_ONTAP_NFS", "FSX_ONTAP_SMB"]
)
#: Decorator that lists FSx for OpenZFS DataSync locations.
datasync_list_fsx_openzfs_locations = _location_list_decorator(
    location_type_filters=["FSX_OPENZFS_NFS"]
)
#: Decorator that lists FSx for Windows DataSync locations.
datasync_list_fsx_windows_locations = _location_list_decorator(
    location_type_filters=["FSX_WINDOWS"]
)
#: Decorator that lists HDFS DataSync locations.
datasync_list_hdfs_locations = _location_list_decorator(location_type_filters=["HDFS"])
#: Decorator that lists NFS DataSync locations.
datasync_list_nfs_locations = _location_list_decorator(location_type_filters=["NFS"])
#: Decorator that lists object-storage DataSync locations.
datasync_list_object_storage_locations = _location_list_decorator(
    location_type_filters=["OBJECT_STORAGE"]
)
#: Decorator that lists S3 and S3 Outposts DataSync locations.
datasync_list_s3_locations = _location_list_decorator(
    location_type_filters=["S3", "OUTPOST_S3"]
)
#: Decorator that lists SMB DataSync locations.
datasync_list_smb_locations = _location_list_decorator(location_type_filters=["SMB"])
