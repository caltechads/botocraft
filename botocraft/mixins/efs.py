from __future__ import annotations

from functools import cached_property, wraps
from typing import TYPE_CHECKING, cast

from botocraft.services.abstract import PrimaryBoto3ModelQuerySet

if TYPE_CHECKING:
    from collections.abc import Callable

    import boto3

    from botocraft.services.common import Tag
    from botocraft.services.ec2 import SecurityGroup
    from botocraft.services.efs import AccessPoint, FileSystem


def _deserialize_tags(raw_tags: list[dict[str, str]] | list[Tag] | None) -> list[Tag]:
    """
    Normalize raw EFS tag payloads into Botocraft ``Tag`` models.

    Args:
        raw_tags: Raw tags returned by boto3 or already-constructed tag models.

    Returns:
        A normalized list of ``Tag`` models.

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


class EFSTagsManagerMixin:
    """
    Shared EFS tag helpers for top-level taggable resources.
    """

    #: Boto3 session associated with this manager.
    session: boto3.session.Session | None

    def _list_resource_tags(self, resource_id: str) -> list[Tag]:
        """
        Return tags for a taggable EFS resource.

        Args:
            resource_id: EFS file-system or access-point identifier.

        Returns:
            The current tags attached to the resource.

        """
        response = self.client.list_tags_for_resource(  # type: ignore[attr-defined]
            ResourceId=resource_id
        )
        return _deserialize_tags(response.get("Tags"))

    def _hydrate_resource_tags(self, resource: FileSystem | AccessPoint | None) -> None:
        """
        Populate the ``Tags`` field on a taggable EFS model.

        Args:
            resource: The file system or access point to enrich.

        Side Effects:
            Updates ``resource.Tags`` in place when a model is provided.

        """
        if resource is None:
            return
        resource_id = cast("str", resource.pk)
        resource.Tags = self._list_resource_tags(resource_id)

    def _sync_resource_tags(self, resource_id: str, tags: list[Tag]) -> None:
        """
        Reconcile a resource's tags with the desired in-memory model state.

        Args:
            resource_id: EFS file-system or access-point identifier.
            tags: Desired final tag set for the resource.

        Side Effects:
            Calls EFS tag and untag APIs to match the desired tag set.

        """
        current_tags = self._list_resource_tags(resource_id)
        current = {tag.Key: tag.Value for tag in current_tags}
        desired = {tag.Key: tag.Value for tag in tags}

        keys_to_remove = sorted(set(current) - set(desired))
        tags_to_upsert = [
            tag for tag in tags if current.get(tag.Key) != tag.Value
        ]

        if keys_to_remove:
            self.client.untag_resource(  # type: ignore[attr-defined]
                ResourceId=resource_id,
                TagKeys=keys_to_remove,
            )
        if tags_to_upsert:
            self.client.tag_resource(  # type: ignore[attr-defined]
                ResourceId=resource_id,
                Tags=self.serialize(tags_to_upsert),  # type: ignore[attr-defined]
            )


def efs_file_system_add_tags(
    func: Callable[..., FileSystem | None],
) -> Callable[..., FileSystem | None]:
    """
    Attach tags to a single EFS file system returned by a manager call.

    Args:
        func: Manager method that returns a single file system.

    Returns:
        A wrapped manager method that hydrates file-system tags.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> FileSystem | None:
        file_system = func(self, *args, **kwargs)
        self._hydrate_resource_tags(file_system)
        return file_system

    return wrapper


def efs_file_systems_add_tags(
    func: Callable[..., PrimaryBoto3ModelQuerySet],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Attach tags to all EFS file systems returned by a manager call.

    Args:
        func: Manager method that returns file systems.

    Returns:
        A wrapped manager method that hydrates tags for each file system.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> PrimaryBoto3ModelQuerySet:
        file_systems = func(self, *args, **kwargs)
        for file_system in file_systems:
            self._hydrate_resource_tags(file_system)
        return file_systems

    return wrapper


def efs_access_point_add_tags(
    func: Callable[..., AccessPoint | None],
) -> Callable[..., AccessPoint | None]:
    """
    Attach tags to a single EFS access point returned by a manager call.

    Args:
        func: Manager method that returns a single access point.

    Returns:
        A wrapped manager method that hydrates access-point tags.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> AccessPoint | None:
        access_point = func(self, *args, **kwargs)
        self._hydrate_resource_tags(access_point)
        return access_point

    return wrapper


def efs_access_points_add_tags(
    func: Callable[..., PrimaryBoto3ModelQuerySet],
) -> Callable[..., PrimaryBoto3ModelQuerySet]:
    """
    Attach tags to all EFS access points returned by a manager call.

    Args:
        func: Manager method that returns access points.

    Returns:
        A wrapped manager method that hydrates tags for each access point.

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> PrimaryBoto3ModelQuerySet:
        access_points = func(self, *args, **kwargs)
        for access_point in access_points:
            self._hydrate_resource_tags(access_point)
        return access_points

    return wrapper


class FileSystemManagerMixin(EFSTagsManagerMixin):
    """
    EFS file-system manager helpers that keep tag state aligned with models.
    """

    if TYPE_CHECKING:

        def get(self, FileSystemId: str) -> FileSystem | None:  # noqa: N803
            """Type hint for the generated manager method."""

    def update(self, model: FileSystem) -> FileSystem:
        """
        Update a file system and optionally reconcile its tags.

        Args:
            model: The file system model to update.

        Side Effects:
            Calls the base EFS update API and, when ``model.Tags`` is provided,
            reconciles remote tags to match the model.

        Returns:
            The refreshed file-system model after the update completes.

        """
        data = model.model_dump(exclude_none=True, by_alias=True)
        args = {
            "FileSystemId": data.get("FileSystemId"),
            "ThroughputMode": data.get("ThroughputMode"),
            "ProvisionedThroughputInMibps": data.get("ProvisionedThroughputInMibps"),
        }
        self.client.update_file_system(  # type: ignore[attr-defined]
            **{key: value for key, value in args.items() if value is not None}
        )
        if model.Tags is not None:
            self._sync_resource_tags(cast("str", model.FileSystemId), model.Tags)
        return cast("FileSystem", self.get(cast("str", model.FileSystemId)))


class AccessPointManagerMixin(EFSTagsManagerMixin):
    """
    EFS access-point manager helpers for tag hydration.
    """


class MountTargetManagerMixin:
    """
    Manager helpers for EFS mount targets that need follow-up EC2 hydration.
    """

    #: Boto3 session associated with this manager.
    session: boto3.session.Session | None

    def get_security_groups(
        self,
        MountTargetId: str,  # noqa: N803
    ) -> PrimaryBoto3ModelQuerySet[SecurityGroup]:
        """
        Return hydrated EC2 security groups for a mount target.

        Args:
            MountTargetId: Mount-target identifier to inspect.

        Returns:
            QuerySet of EC2 security groups attached to the mount target.

        """
        from botocraft.services.ec2 import SecurityGroup

        response = self.client.describe_mount_target_security_groups(  # type: ignore[attr-defined]
            MountTargetId=MountTargetId
        )
        group_ids = response.get("SecurityGroups", [])
        if not group_ids:
            return PrimaryBoto3ModelQuerySet([])
        return SecurityGroup.objects.using(self.session).list(GroupIds=group_ids)


class MountTargetModelMixin:
    """
    Convenience helpers for EFS mount targets that are not practical to generate.
    """

    #: File-system identifier used for relation lookups.
    FileSystemId: str
    #: Mount-target identifier used for follow-up helper calls.
    MountTargetId: str
    #: Boto3 session associated with this resource.
    session: boto3.session.Session | None

    @cached_property
    def security_groups(self) -> PrimaryBoto3ModelQuerySet[SecurityGroup]:
        """
        Return hydrated EC2 security groups attached to this mount target.

        Returns:
            QuerySet of EC2 security groups attached to this mount target.

        """
        return self.objects.using(self.session).get_security_groups(  # type: ignore[attr-defined]
            self.MountTargetId
        )

    def set_security_groups(
        self,
        SecurityGroups: list[str],  # noqa: N803
    ) -> None:
        """
        Replace security groups attached to this mount target.

        Args:
            SecurityGroups: Security-group IDs to attach to the mount target.

        Side Effects:
            Updates the mount target's security-group associations in AWS.

        """
        self.objects.using(self.session).modify_security_groups(  # type: ignore[attr-defined]
            self.MountTargetId,
            SecurityGroups,
        )
